#! /usr/bin/env python

import random
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

def reportdevice(uuid='488a0d5b-c0d3-415c-8daa-a2a4fd3261f4', type='switch', product='aGoControl simulator device'):
	try:
		content = {}
		content["devicetype"]=type
		content["uuid"] = uuid
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

def sendtempevent(uuid, temp):
        try:
                content = {}
                content["uuid"] = uuid
                content["level"] = float(temp)
                content["unit"] = "degC"
                message = Message(content=content,subject="event.environment.temperaturechanged")
                sender.send(message)
        except SendError, e:
                print e

def sendSensorTriggerEvent(uuid, level):
        try:
                content = {}
                content["uuid"] = uuid
                content["level"] = level
                message = Message(content=content,subject="event.security.sensortriggered")
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

syslog.syslog(syslog.LOG_NOTICE, "agosimulator.py startup")

devices = {}
devices["2ab0e80d-7b48-4d17-b083-58fda121d6e3"] = "switch"
devices["40cbb44c-5997-4f30-b1f5-d4d6c2accfad"] = "switch"
devices["52abead4-82b0-4fd2-ac3a-c9de1cb12b9b"] = "dimmer"
devices["69fac346-875f-4a80-b9af-c53459cc13dd"] = "multilevelsensor"
devices["5194cdcb-8d81-4d3c-a12f-19c554a70b1f"] = "dimmerrgb"
devices["e3a5c630-12bf-4956-8d1f-1da1dfd31c0a"] = "zwavecontroller"

def discovery():
	for (uuid, devicetype) in devices.iteritems():
		reportdevice(uuid=uuid, type=devicetype)

discovery()

counter = 1

while True:
	counter = counter + 1
	try:
		if counter > 15:
			counter = 0
			temp = random.randint(50,300) / 10
			sendtempevent("69fac346-875f-4a80-b9af-c53459cc13dd", temp)		
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
						for (uuid, devicetype) in devices.iteritems():
							if message.content['uuid'] == uuid:
								# print path, uuid
								command = ''
								if message.content['command'] == 'on':
									sendStateChangedEvent(uuid, 255)
									print "device switched on"
								if message.content['command'] == 'off':
									sendStateChangedEvent(uuid, 0)
									print "device switched off"
								if message.content['command'] == 'setlevel':
									if 'level' in message.content:
										sendStateChangedEvent(uuid, message.content["level"])
										print "device level changed", message.content["level"]
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




