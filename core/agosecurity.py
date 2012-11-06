#! /usr/bin/env python

import sys
import syslog
import time
import pickle
import optparse
import ConfigParser
import uuid

from array import array

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

try:
	securitypin = config.get("security","pin")
except ConfigParser.NoOptionError, e:
	securitypin = "1234"
except ConfigParser.NoSectionError, e:
	securitypin = "1234"

try:
	securitypin = config.get("security","silentpin")
except ConfigParser.NoOptionError, e:
	silentpin = "4321"
except ConfigParser.NoSectionError, e:
	silentpin = "4321"

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

try:
	securitymapfile = open("/etc/opt/agocontrol/security.pck","r")
	securitymap = pickle.load(securitymapfile)
	securitymapfile.close()
except IOError, e:
	securitymap = {}

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

def savemap():
	try:
		securitymapfile = open("/etc/opt/agocontrol/security.pck","w")
		pickle.dump(securitymap, securitymapfile)
		securitymapfile.close()
	except IOError, e:
		pass

def reportdevice(uuid, type='securitysystem', product='aGoControl security system'):
	try:
		content = {}
		content["devicetype"]=type
		content["uuid"] = uuid
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

syslog.syslog(syslog.LOG_NOTICE, "agosecurity.py startup")

if 'myuuid' not in securitymap:
	securitymap["uuid"] = str(uuid.uuid4())
	savemap()

reportdevice(securitymap["uuid"])

while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.content:
			if 'command' in message.content:
				if message.content['command'] == 'discover':
					syslog.syslog(syslog.LOG_NOTICE, "device discovery")
					reportdevice(securitymap["uuid"])
				if 'uuid' in message.content and 'pin' in message.content and 'mode' in message.content:
					uuid = message.content['uuid']
					if uuid == securitymap["uuid"] and message.content['command'] == 'sethousemode' and message.content["pin"] == securitypin:
						securitymap["mode"] = message.content["mode"]
						savemap()
						syslog.syslog(syslog.LOG_NOTICE, "house mode changed")
						print "house mode changed"
	except Empty, e:
		pass
	except ReceiverError, e:
		print e
		time.sleep(1)
