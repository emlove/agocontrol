#!/usr/bin/env python
#
# resolver - service and name resolver for the AMQP based automation control
#
# Copyright (c) 2012 Harald Klein <hari@vt100.at>
#

import sys
import syslog
import ConfigParser, os

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

# load device inventory from inventory.py
import inventory as inv

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
	schemafile = config.get("system","schema")
except ConfigParser.NoOptionError, e:
	schemafile = "/etc/opt/agocontrol/schema.yaml"

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

# route stderr to syslog
class LogErr:
	def write(self, data):
		syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
sys.stderr = LogErr()
sys.stdout = LogErr()

# load schema
schemastream = file(schemafile, 'r')
schema = load(schemastream, Loader=Loader)

content = {}
content["command"] = "discover"

inventory = {}

connection = Connection(broker, username=username, password=password, reconnect=True)
try:
	connection.open()
	session = connection.session()
	# we use a topic exchange
	sender = session.sender("agocontrol; {create: always, node: {type: topic}}")
	receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")

	# send discover message to get device announce notifications
	message = Message(content=content)
	sender.send(message)

	while True:
		try:
			message = receiver.fetch()
			# print message.subject
			if message.content:
				if 'command' in message.content:
					if message.content["command"]=="inventory":
						syslog.syslog(syslog.LOG_NOTICE, "listing inventory")
						content = {}
						content["schema"] = schema
						content["inventory"] = inventory
						content["rooms"] = inv.getrooms()
						# syslog.syslog(syslog.LOG_NOTICE, str(content))
						try:
							replysender = session.sender(message.reply_to)
							reply = Message(content=content)
							replysender.send(reply)
						except SendError, e:
							print e
						except MalformedAddress, e:
							print e
						except NotFound, e:
							print e
					elif message.content["command"]=="setroomname":
						try:
							myuuid = ""
							if "uuid" in message.content:
								myuuid = message.content["uuid"]
							else:
								myuuid = str(uuid4())	
							inv.setroomname(myuuid,message.content["name"])
							try:
								replysender = session.sender(message.reply_to)
								reply = Message(content=myuuid)
								replysender.send(reply)
							except SendError, e:
								print e
							except MalformedAddress, e:
								print e
							except NotFound, e:
								print e
						except KeyError, e:
							print e
					elif message.content["command"]=="setdeviceroom":
						try:
							syslog.syslog(syslog.LOG_NOTICE, "command setdeviceroom")
							inv.setdeviceroom(message.content["uuid"],message.content["room"])
							inventory[message.content["uuid"]]["room"] = inv.getdeviceroom(message.content["uuid"])
							try:
								replysender = session.sender(message.reply_to)
								reply = Message(content="OK")
								replysender.send(reply)
							except SendError, e:
								print e
							except MalformedAddress, e:
								print e
							except NotFound, e:
								print e
						except KeyError, e:
							print e
					elif message.content["command"]=="setdevicename":
						try:
							inv.setdevicename(message.content["uuid"],message.content["name"])
							inventory[message.content["uuid"]]["name"] = inv.getdevicename(message.content["uuid"])
							try:
								replysender = session.sender(message.reply_to)
								reply = Message(content="OK")
								replysender.send(reply)
							except SendError, e:
								print e
							except MalformedAddress, e:
								print e
							except NotFound, e:
								print e
						except KeyError, e:
							print e
					elif message.content["command"]=="deleteroom":
						try:
							myuuid = message.content["uuid"]
							inv.deleteroom(myuuid)
							try:
								replysender = session.sender(message.reply_to)
								reply = Message(content="OK")
								replysender.send(reply)
							except SendError, e:
								print e
							except MalformedAddress, e:
								print e
							except NotFound, e:
								print e
						except KeyError, e:
							print e
			if message.subject:
				if 'event' in message.subject:
					if message.subject=="event.device.announce":
						if 'devicetype' in message.content:
							if 'uuid' in message.content:
								uuid = message.content["uuid"]
								element = {}
								element["name"] = inv.getdevicename(uuid)
								element["room"] = inv.getdeviceroom(uuid)
								element["devicetype"] = message.content["devicetype"]
								element["state"] = 0
								inventory[uuid]=element
					if message.subject=="event.device.remove":
						if 'uuid' in message.content:
							uuid = message.content["uuid"]
							if uuid in inventory:
								del inventory[uuid]
					if message.subject=="event.device.statechanged":
						if 'uuid' in message.content:
							if 'level' in message.content:
								uuid = message.content["uuid"]
								level = message.content["level"]
								if uuid in inventory:
									inventory[uuid]["state"] = level
					if message.subject == "event.environment.temperaturechanged":
						if 'uuid' in message.content:
							if 'level' in message.content:
								uuid = message.content["uuid"]
								if uuid in inventory:
									inventory[uuid]["state"] = message.content["level"]
			session.acknowledge()
		except TypeError, e:
			print "TypeError in message handling: ", e
		except Empty:
			pass
except SendError, e:
	print e
except ReceiverError, e:
	print e
except KeyboardInterrupt:
	pass
finally:
	connection.close()
