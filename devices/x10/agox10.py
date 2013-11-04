#!/usr/bin/python

import agoclient
import threading
import time
import logging

from x10.controllers.cm11 import CM11

dev = CM11(agoclient.getConfigOption("x10", "device", "/dev/ttyUSB1"))
dev.open()

#  Dictionaries to decrypt hex values sent from CM11A to house/device codes as well as function on/off
#  Other functions exist but on/off are the only ones handled.  All other functions are ignored
#  Functions are displayed as decimal values ON = 255 and OFF = 0
#  See http://www.smarthome.com/manuals/protocol.txt for details

x10_house =  {'6': 'A', 'e': 'B', '2': 'C', 'a': 'D', '1': 'E', '9': 'F', '5': 'G', 'd': 'H', '7': 'I', 'f': 'J', '3': 'K', 'b': 'L', '0': 'M', '8': 'N', '4': 'O', 'c': 'P'}
x10_device = {'6': '1', 'e': '2', '2': '3', 'a': '4', '1': '5', '9': '6', '5': '7', 'd': '8', '7': '9', 'f': '10', '3': '11', 'b': '12', '0': '13', '8': '14', '4': '15', 'c': '16'}
x10_funct  = {'2': '255', '3': '0'}


client = agoclient.AgoConnection("X10")

# This section handles sending X10 devices over the CM11A using Python-X10

# this class will be instantiated and spawned into background to not block the messageHandler
x10lock = threading.Lock()

class x10send(threading.Thread):
	def __init__(self, id, functioncommand, level):
		threading.Thread.__init__(self)
		self.id = id
		self.functioncommand = functioncommand
		self.level = level
	def run(self):
		if self.functioncommand == "on":
			print "switching on: " + self.id
			x10lock.acquire()
			dev.actuator(self.id).on()
			x10lock.release()
			client.emitEvent(self.id, "event.device.statechanged", "255", "")
		if self.functioncommand == "off":
			print "switching off: " + self.id
			x10lock.acquire()
			dev.actuator(self.id).off()
			x10lock.release()
			client.emitEvent(self.id, "event.device.statechanged", "0", "")

		if self.functioncommand == "setlevel":
			print "Dimming: " + self.id
			x10lock.acquire()
			dev.actuator(self.id).dim(self.level)
			x10lock.release()
			client.emitEvent(self.id, "event.device.statechanged", self.level, "")


def messageHandler(internalid, content):
	if "command" in content:
		if "level" in content:
			background = x10send(internalid, content["command"], content["level"])
		else:
			background = x10send(internalid, content["command"], "")
		background.setDaemon(True)
		background.start()

# specify our message handler method
client.addHandler(messageHandler)

# X10 device configuration
readSwitches = agoclient.getConfigOption("x10", "switches", "A2,A3,A9,B3,B4,B5,B9,B12") 
switches = map(str, readSwitches.split(',')) 
for switch in switches: 
	client.addDevice(switch, "switch")
readDimmers = agoclient.getConfigOption("x10", "dimmers", "D1") 
dimmers = map(str, readDimmers.split(',')) 
for dimmer in dimmers: 
	client.addDevice(dimmer, "dimmer")

# This section is used to monitor for incoming RF signals on the CM11A


class readX10(threading.Thread):
	def __init__(self,):
		threading.Thread.__init__(self)
	def run(self):
		loop=1
		while (loop == 1):
			x10lock.acquire()
			data=dev.read()
			x10lock.release()
			# Check to see if the CM11A received a command
			if (data == 90):
				# Send 0xc3 to CM11A to tell it to send the data
				x10lock.acquire()
				dev.write(0xc3)

				# Read the data.  This should be modified as this code only reads
				# The first four bytes

				# The first byte send tells how many bytes to expect
				first=dev.read()
				first="%x"%(first)
				first=int(first)

				received=[]
				for i in range(first):
					readvalue = dev.read()
					received.append(readvalue)

				# From the list we read how many elements we expect
				totalexpected="%x"%(received[0])

				# device address (ie B2)
				receivedaddress="%x"%(received[1])

				# function (ie ON)
				receivedfunction="%x"%(received[2])

				x10lock.release()

				# Make sure that we are only handling on/off requests
				if (totalexpected == '2'):
					print x10_house[receivedaddress [:1]] + x10_device[receivedaddress [1:]] + " " + x10_funct[receivedfunction [1:]];
					# Look up values in dicitionaries and assign variables
					send_x10_address = x10_house[receivedaddress [:1]] + x10_device[receivedaddress [1:]];
					send_x10_command = x10_funct[receivedfunction [1:]];

					# Use these values to change device states in Ago Control
					if (send_x10_command == "0") or (send_x10_command == "255"):
						client.emitEvent(send_x10_address , "event.device.statechanged", send_x10_command , "");
					else:
						print "Unknown command received"

background = readX10()
background.setDaemon(True)
background.start()

client.run()
