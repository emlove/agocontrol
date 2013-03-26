#! /usr/bin/env python
#
# ago INIM device
# Copyright (c) 2013 by rages
#
#/etc/opt/agocontrol/config.ini
#
#[INIM]
#terminal=10
#outputs=0
#
# Interface for security panels from INIM: http://www.inim.biz
#
# the terminals connected to the control unit can be up to 100
# the base unit without expansion has 10
# 

import agoclient
import time
import threading
import serial

client = agoclient.AgoConnection("INIM")

port = agoclient.getConfigOption("INIM", "port", "/dev/ttyS0")
terminal = int(agoclient.getConfigOption("INIM", "terminal", "10"))
outputs = agoclient.getConfigOption("INIM", "outputs", "3")

# add devices for terminals
for i in range(terminal):
	id = i+1
	client.addDevice("%d" % (id), "binarysensor")


ser = serial.Serial(port, 57600, parity=serial.PARITY_EVEN, stopbits=1, timeout=1)

class requestZoneStatus(threading.Thread):
	def __init__(self,):
		threading.Thread.__init__(self)
	def run(self):
		while(True):
			#request zone status
			ser.write('\x00\x00\x00\x20\x01\x00\x1A\x3B') #sends the request to the alarm panel
			# the panel responds with 25 bytes:
			# 1 byte =  4 terminals (2 bit for status)
			# 4 x 25 = 100 terminals
			stato_t = ser.read(27)
			i = 0
			zn = 1
			while i < 25:
				c = bin(ord(stato_t[i]))[2:].zfill(8)
				#read the state of terminal (2 bit)
				z = 1
				zb = 0
				while z < 5:
			  		z1 = c[0+zb]+c[1+zb]
			  		if z1 == "00":
			 			print "zone", zn, "in short"
					elif z1 == "01":
						print "zone", zn, "retired"
						client.emitEvent(zn, "event.security.sensortriggered", 0, "")
					elif z1 == "10":
						print "zone", zn, "in alarm"
						client.emitEvent(zn, "event.security.sensortriggered", 255, "")
					else :
						print "zone", zn, "sabotage"

					if (zn == terminal):
						z = 5
						i = 25
					else :
						zn = zn + 1
						z = z + 1
						zb = zb + 2

					i = i + 1
			time.sleep(1)

background = requestZoneStatus()
background.setDaemon(True)
background.start()

client.run()

ser.close()
