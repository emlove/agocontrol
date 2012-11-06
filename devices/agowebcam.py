#! /usr/bin/env python

import random
import sys
import syslog
import time
import pickle
import optparse
import ConfigParser
import socket

import urllib2
from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
	username = config.get("system","username")
except ConfigParser.NoOptionError, e:
	username = "agocontrol"

try:
	password = config.get("system","password")
except ConfigParser.NoOptionError, e:
	password = "letmein"

try:
	broker = config.get("system","broker")
except ConfigParser.NoOptionError, e:
	broker = "localhost"

try:
	debug = config.get("system","debug")
except ConfigParser.NoOptionError, e:
	debug = "WARN"

if debug=="DEBUG":
	enable("qpid", DEBUG)
else:
	enable("qpid", WARN)

 
parser = optparse.OptionParser(usage="usage: %prog <command> [options] [ PARAMETERS ... ]",
                               description="send automation control commands")
parser.add_option("-b", "--broker", default=broker, help="hostname of broker (default %default)")
parser.add_option("-u", "--username", default=username, help="specify a username")
parser.add_option("-P", "--password", default=password, help="specify a password")

opts, args = parser.parse_args()

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

def reportdevice(uuid, type='camera', product='IP Camera'):
	try:
		content = {}
		content["devicetype"]=type
		content["uuid"] = uuid
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

def sendStateChangedEvent(uuid, level):
        try:
                content = {}
                content["uuid"] = uuid
                content["level"] = level
                message = Message(content=content,subject="event.device.statechanged")
                sender.send(message)
        except SendError, e:
                print e

syslog.syslog(syslog.LOG_NOTICE, "agowebcam.py startup")

devices = {}
devices["2ab0e80d-7b48-4d17-b083-58fda121d6e4"] = "http://192.168.80.3/axis-cgi/jpg/image.cgi?resolution=640x480"

def discovery():
	for (uuid, url) in devices.iteritems():
		reportdevice(uuid=uuid)

discovery()


while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.content:
			if 'command' in message.content:
				print message
				if message.content['command'] == 'discover':
					syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
					discovery()
				elif message.content['command'] == 'inventory':
					syslog.syslog(syslog.LOG_NOTICE, "ignoring inventory command")
				else:
					if 'uuid' in message.content:
						for (uuid, url) in devices.iteritems():
							if message.content['uuid'] == uuid:
								if message.content['command'] == 'getvideoframe' and message.reply_to:
									print "getting video frame"
									u = urllib2.urlopen(url)	
									buffer = u.read()
									replysender = session.sender(message.reply_to)
									response = Message(buffer)
									response.content_type="image/jpg"
									try:
										replysender.send(response)
									except SendError, e:
										print "Can't send ACK: ", e
	except Empty, e:
		pass
	except KeyError, e:
		print "key error in command evaluation", e
	except ReceiverError, e:
		print e
		time.sleep(1)




