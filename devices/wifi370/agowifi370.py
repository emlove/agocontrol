#!/usr/bin/env python

import socket
import agoclient

client = agoclient.AgoConnection("wifi370")

COMMAND_ON="\xcc\x23\x33"
COMMAND_OFF="\xcc\x24\x33"
# COMMAND_RGB="\x56\xRR\xGG\xBB\xaa"
COMMAND_STATUS="\xef\x01\x77"
try:
	deviceconfig = agoclient.getConfigOption("wifi370", "devices", "192.168.80.44:5577")
	devices = map(str, deviceconfig.split(','))
except e:
	devices = None
	print "Error, no devices:" + e
else:
	for device in devices:
		client.addDevice(device, "dimmerrgb")

def sendcmd(host, port, command):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		s.send(command)
		s.close()
	except socket.error as msg:
		print "Socket error: ", msg

def getstatus(host, port):
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((host, port))
		s.send(COMMAND_STATUS)
		reply = s.recv(11)
		s.close()
		if ord(reply[0])==0x66 and ord(reply[10]) == 0x99:
			red = ord(reply[6])
			green = ord(reply[7])
			blue = ord(reply[8])
			if ord(reply[2])==0x23:
				onoff=255
			else:
				onoff=0
			# mode = ord(reply[3])
			# startstop = ord(reply[4])
			# usermem = ord(reply[9])
			return (onoff, red, green, blue)
		else:
			print "ERROR: cannot get status from " + host + ":" + port
	except socket.error as msg:
		print "Socket error: ", msg

def messageHandler(internalid, content):
	host, _port = internalid.split(':')
	port = int(_port)
	if "command" in content:
		if content["command"] == "on":
			print "switching on: " + internalid
			sendcmd(host,port,COMMAND_ON)
			try:
				(onoff, red, green, blue) = getstatus(host, port)
				client.emitEvent(internalid, "event.device.statechanged", str(onoff), "")
			except TypeError:
				print "ERROR: Can't read status"
		if content["command"] == "off":
			print "switching off: " + internalid
			sendcmd(host,port,COMMAND_OFF)
			try:
				(onoff, red, green, blue) = getstatus(host, port)
				client.emitEvent(internalid, "event.device.statechanged", str(onoff), "")
			except TypeError:
				print "ERROR: Can't read status"
		if content["command"] == "setlevel":
			level = content["level"]
			print "setting level:", internalid, level
			value = int(level) * 255 / 100
			command = "\x56" + chr(value) + chr(value) + chr(value) + "\xaa"
			sendcmd(host,port,COMMAND_ON)
			sendcmd(host,port,command)
			try:
				(onoff, red, green, blue) = getstatus(host, port)
				if onoff == 0:
					client.emitEvent(internalid, "event.device.statechanged", str(onoff), "")
				else:
					client.emitEvent(internalid, "event.device.statechanged", str((red + green + blue)*100/3/255), "")
			except TypeError:
				print "ERROR: Can't read status"
			client.emitEvent(internalid, "event.device.statechanged", level, "")
		if content["command"] == "setcolor":
			red = int(content["red"]) * 255 / 100
			green = int(content["green"]) * 255 / 100
			blue = int(content["blue"]) * 255 / 100
			command = "\x56" + chr(red) + chr(green) + chr(blue) + "\xaa"
			sendcmd(host,port,COMMAND_ON)
			sendcmd(host,port,command)
			try:
				(onoff, red, green, blue) = getstatus(host, port)
				if onoff == 0:
					client.emitEvent(internalid, "event.device.statechanged", str(onoff), "")
				else:
					client.emitEvent(internalid, "event.device.statechanged", str((red + green + blue)*100/3/255), "")
					#client.emitEvent(internalid, "event.device.statechanged", str(red) + "/" + str(green) + "/" + str(blue), "")
			except TypeError:
				print "ERROR: Can't read status"

client.addHandler(messageHandler)

print "Waiting for messages"
client.run()

