#!/usr/bin/env python
# Melloware Lighswitch interface
# Protocol definition for the "Lightswitch" iPhone App: http://forum.melloware.com/viewtopic.php?f=15&t=7977

# This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; 
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# See the GNU General Public License for more details.

# Copyright (c) 2012 Harald Klein <hari@vt100.at>

# Only devices supported atm, no rooms or scenes, more to come..
 
import socket
import re
import threading
import optparse

import ConfigParser
from qpid.messaging import * 
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


# This should point to the host where DCERouter/RPC-Plugin is running
connection = Connection(broker, username=username, password=password, reconnect=True)
connection.open() 
session = connection.session()
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

TCP_PORT=6004
BUFFER_SIZE=4096

class ClientThread ( threading.Thread ):
	def __init__ ( self, conn, addr ):
		self.conn = conn
		self.addr = addr
		threading.Thread.__init__ ( self )

	def run ( self ):
		print 'Received connection:', self.addr [0]
		data = self.conn.recv(BUFFER_SIZE)
		if not data:
			print "ERROR: no data, closing connection\n"
			self.conn.close()
			return
		m=re.match("IPHONE",data)
		if not m: 
			print "ERROR: invalid client, closing connection\n"
			self.conn.close()
			return
		print "received data:", data
		self.conn.send('COOKIE~40821\n')  # echo
		data = self.conn.recv(BUFFER_SIZE)
		if not data: return
		print "received data:", data
		self.conn.send('VER~1.1.3290.16502\n')  # echo
		data = self.conn.recv(BUFFER_SIZE)
		if not data: return

		# fetch data
		print "fetching device list"
		replyuuid = str(uuid4())
		receiver = session.receiver("reply-%s; {create: always, delete: always}" % replyuuid)
		content = {}
		content["command"] = "inventory"
		try:
			message = Message(content=content)
			message.reply_to = "reply-%s" % replyuuid
			sender.send(message)
		except SendError, e:
			print e
		try:
			message = receiver.fetch(timeout=10)
		except ReceiveError, e:
			print e

		print "received data:", message
		for id, device in message.content["inventory"].iteritems():
			state = 0
			state=device['state']
			try:
				if devie['name'] != "":
					if device['devicetype'] == "switch":
						# print device['description']
						self.conn.send("DEVICE~%s~%s~%d~BinarySwitch\n" % (device['name'],id,state ))  # echo
					if device['devicetype'] == "dimmer":
						# print device['description']
						self.conn.send("DEVICE~%s~%s~%d~MultilevelSwitch\n" % (device['name'],id,state ))  # echo
					if device['devicetype'] == "drapes":
						# print device['description']
						self.conn.send("DEVICE~%s~%s~%d~WindowCovering\n" % (device['name'],id,state ))  # echo
			except KeyError, e:
				print e
		# self.conn.send('DEVICE~RPCState~0~0~STATUS\n')  # echo
		# self.conn.send('DEVICE~Temper~0~27~THERMOMETER\n')  # echo
		# self.conn.send('DEVICE~Sensor~0~1~SENSOR\n')  # echo
		self.conn.send('ENDLIST\n')  # echo
		while True:
			data = self.conn.recv(BUFFER_SIZE)
			if not data: break
			print "received data:", data
			# DEVICE~251~100~MultilevelSwitch
			m = re.match("DEVICE~(.*?)~(\d+)~",data)
			device=""
			level=0
			if m:
				device = m.group(1)
				level = int(m.group(2))
			# print "device", device, "level", level
			content={}
			content["uuid"]=device
			content["level"]=level
			if level == 0:
				print "switching off", device
				content["command"] = "off"
			if level == 255:
				print "switching on", device
				content["command"] = "on"
			if 0<level<101:
				print "setlevel", device, level
				content["command"] = "setlevel"
			message = Message(content=content)
			try:
				sender.send(message)
			except SendError, e:
				print e
		print 'Closing connection:', self.addr [0]
		self.conn.close()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.bind(('', TCP_PORT))
s.listen(5)

print "LightSwitch2AMQP startup\n"

while True:
	conn, addr = s.accept()
	ClientThread (conn, addr).start()

