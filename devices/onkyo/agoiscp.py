#! /usr/bin/env python

import sys
import syslog
import time
import pickle
import optparse
import ConfigParser
import socket

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from core import eISCP
import commands

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
	username = config.get("system","username")
except:
	username = "agocontrol"

try:
	password = config.get("system","password")
except:
	password = "letmein"

try:
	broker = config.get("system","broker")
except:
	broker = "localhost"

try:
	debug = config.get("system","debug")
except:
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

# read persistent uuid mapping from file
try:
	uuidmapfile = open("/etc/agocontrol/iscp-uuidmap.pck","r")
	uuidmap = pickle.load(uuidmapfile)
	uuidmapfile.close()
except IOError, e:
	uuidmap = {}

devices = {}

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

def lookupuuid(path):
	if path in uuidmap:
		pass
	else:
		newuuid = str(uuid4())
		uuidmap[path] = newuuid
		try:
			# uuid is new, try to store it
			uuidmapfile = open("/etc/opt/agocontrol/iscp-uuidmap.pck","w")
			pickle.dump(uuidmap, uuidmapfile)
			uuidmapfile.close()
		except IOError, e:
			pass
	return uuidmap[path]

def reportdevice(path, type='avreceiver', product='Onkyo AVR'):
	try:
		content = {}
		content["devicetype"]=type
		content["event"] = "announce"
		content["uuid"] = lookupuuid(path)
		content["internal-id"] = path
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

def discovery(timeout=1):
	avrs = eISCP.discover(timeout)
	for avr in avrs:
		reportdevice("%s:%s" % (avr.host, avr.port), product=avr.info['model_name']);

syslog.syslog(syslog.LOG_NOTICE, "agoiscp.py startup")

syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
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
				if message.content['command'] == 'inventory':
					syslog.syslog(syslog.LOG_NOTICE, "ignoring inventory command")
				else:
					for (path, uuid) in uuidmap.iteritems():
						if message.content['uuid'] == uuid:
							avr = eISCP(str.split(path,':',2)[0], int(str.split(path,':',2)[1]))
							command = ''
							try:
								if message.content['command'] == 'on':
									command = 'system-power:on'
									avr.command(command)
								if message.content['command'] == 'off':
									command = 'system-power:standby'
									avr.command(command)
								if message.content['command'] == 'mute':
									command = 'audio-muting:on'
									avr.command(command)
								if message.content['command'] == 'unmute':
									command = 'audio-muting:off'
									avr.command(command)
								if message.content['command'] == 'mutetoggle':
									command = 'audio-muting:toggle'
									avr.command(command)
								if message.content['command'] == 'vol+':
									command = 'master-volume:level-up'
									avr.command(command)
								if message.content['command'] == 'vol-':
									command = 'master-volume:level-down'
									avr.command(command)
								if message.content['command'] == 'setlevel':
									if 'level' in message.content:
										level = int(message.content['level'])
										command = 'MVL%x' % level
										# print "sending raw", command
										avr.send_raw(command)
								if message.content['command'] == 'setinput':
									if 'input' in message.content:
										command = 'input-selector:%s' % message.content['input']
										avr.command(command)
							except ValueError, e:
								print e
							# send reply
							if message.reply_to:
								replysender = session.sender(message.reply_to)
								response = Message("ACK")
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




