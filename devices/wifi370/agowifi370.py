#!/usr/bin/env python

import socket
import agoclient

client = agoclient.AgoConnection("wifi370")

COMMAND_ON="\xcc\x23\x33"
COMMAND_OFF="\xcc\x24\x33"
# COMMAND_RGB="\x56\xRR\xGG\xBB\xaa"

try:
	deviceconfig = agoclient.getConfigOption("wifi370", "devices", "192.168.80.44:5577")
	devices = map(str, deviceconfig.split(','))
except e:
	devices = None
	print "Error, no devices:" + e
else:
	for device in devices:
		client.addDevice(device, "dimmerrgb")

def sendtcp(host, port, command):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	s.send(command)
	s.close()

def messageHandler(internalid, content):
	host, _port = internalid.split(':')
	port = int(_port)
	if "command" in content:
		if content["command"] == "on":
			print "switching on: " + internalid
			sendtcp(host,port,COMMAND_ON)
			client.emitEvent(internalid, "event.device.statechanged", "255", "")
		if content["command"] == "off":
			print "switching off: " + internalid
			sendtcp(host,port,COMMAND_OFF)
			client.emitEvent(internalid, "event.device.statechanged", "0", "")
		if content["command"] == "setlevel":
			level = content["level"]
			print "setting level: " + level
			value = int(level) * 255 / 100
			command = "\x56" + chr(value) + chr(value) + chr(value) + "\xaa"
			sendtcp(host,port,command)
			client.emitEvent(internalid, "event.device.statechanged", level, "")
		if content["command"] == "setcolor":
			red = int(content["red"]) * 255 / 100
			green = int(content["green"]) * 255 / 100
			blue = int(content["blue"]) * 255 / 100
			command = "\x56" + chr(red) + chr(green) + chr(blue) + "\xaa"
			sendtcp(host,port,command)
			client.emitEvent(internalid, "event.device.statechanged", str((red + green + blue) / 255 * 33), "")
			

client.addHandler(messageHandler)

print "Waiting for messages"
client.run()

