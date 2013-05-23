#!/usr/bin/python

import time
import threading
import socket
import struct
import re

import agoclient

GC100_ANNOUNCE_MCAST_IP="239.255.250.250"
GC100_ANNOUNCE_PORT=9131
GC100_COMM_PORT=4998

BUFFER_SIZE=8192

client = agoclient.AgoConnection("gc100")

devices = {}

def sendcommand(host, port, command):
	# print "connecting to", host, "port", port
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((host, port))
	s.send(command)
	data = s.recv(BUFFER_SIZE)
	s.close()
	return data

def getdevices(host, port):
	return sendcommand(host, port, "getdevices\r")

def getir(host, port, addr):
	return sendcommand(host, port , "get_IR,%s" % addr)

def setstate(host, port, addr, state):
	return sendcommand(host, port, "setstate,%s,%i\r" % (addr, state))

def discover(arg, stop):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('', GC100_ANNOUNCE_PORT))
	mreq = struct.pack("4sl", socket.inet_aton(GC100_ANNOUNCE_MCAST_IP), socket.INADDR_ANY)

	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

	print "Listening for GC100 devices"
	while(not stop.is_set()):
		data, addr = sock.recvfrom(1024)
		m = re.search("<-Model=(.*?)>", data)
		model = m.group(1)
		m = re.search("<Config-URL=http://(.*?)>", data)
		address = m.group(1)
		if address not in devices:
			print "Found", model, "on", address
			devices[address]=model;

stop = threading.Event()
t = threading.Thread(target=discover,args=(1,stop))
t.daemon = True
t.start()
time.sleep(63)
stop.set()
t.join()
print "finished discovery"

class WatchInputs(threading.Thread):
	def __init__(self, addr):
		threading.Thread.__init__(self)
		self.addr = addr
	def run(self):
		print "Watching inputs on", self.addr
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((self.addr, GC100_COMM_PORT))
		while(True):
			data = s.recv(BUFFER_SIZE)
			print data
			try:
				event, module, state = str(data).split(',')
				if 'statechange' in event:
					if '0' in state:
						client.emitEvent("%s/%s" % (self.addr, module), "event.device.statechanged", 255, "")
					else:
						client.emitEvent("%s/%s" % (self.addr, module), "event.device.statechanged", 0, "")
			except ValueError, e:
				print "value error", e, data
		s.close()
		
for addr in devices:
	print "Scanning", devices[addr], "on", addr
	devicestr= str(getdevices(addr, GC100_COMM_PORT))
	for device in devicestr.split('\r'):
		if 'endlistdevices' in device:
			break;
		print device
		try:
			dev, module, type = device.split(',')
			if '3 RELAY' in type:
				for x in range(1, 4):
					client.addDevice("%s/%s:%i" % (addr, module, x), "switch")
			if '3 IR' in type:
				for x in range(1, 4):
					if 'SENSOR_NOTIFY' in getir(addr, GC100_COMM_PORT, "%s:%i" % (module, x)):
						client.addDevice("%s/%s:%i" % (addr, module, x), "binarysensor")
		except ValueError, e:
			print "value error", e, data

	notificationThread = WatchInputs(addr)
	notificationThread.setDaemon(True)
	notificationThread.start()

def messageHandler(internalid, content):
	addr, connector = internalid.split('/')
	if "command" in content:
		if content["command"] == "on":
			print "switching on: " + internalid
			reply = setstate(addr, GC100_COMM_PORT, connector, 1)
			# state,3:1,1
			name, tmpconn, state = reply.split(',')
			if "1" in state:
				client.emitEvent(internalid, "event.device.statechanged", "255", "")
		if content["command"] == "off":
			print "switching off: " + internalid
			reply =  setstate(addr, GC100_COMM_PORT, connector, 0)
			name, tmpconn, state = reply.split(',')
			if "0" in state:
				client.emitEvent(internalid, "event.device.statechanged", "0", "")

client.addHandler(messageHandler)

print "Waiting for messages"
client.run()

