#! /usr/bin/env python
# JointSpace compatible devices - Philips TV sets > 2010, Blueray Players, ... (http://jointspace.sourceforge.net)

import sys
import syslog
import pickle
import optparse
import ConfigParser

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

import thread
import time

import select
import urllib2
import json
import binascii
import uuid
import signal

from socket import *
from struct import *

# get this device UUID by using MAC address. Used only for discovery broadcasts to not recognize ourselves as player device
myUUID = uuid.uuid1()

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
	jointspacehost = config.get("jointspace","device")
except:
	jointspacehost = "localhost"

try:
	jointspaceport = int(config.get("jointspace","port"))
except:
	jointspaceport = 1925

try:
	voodooPort = int(config.get("jointspace","voodooport"))
except:
	voodooPort = 2323
	
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

class deviceInfo:
	pass

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

# Update store (pickle file) and set name if new device
def updateDevice(deviceUUID, deviceIP, deviceName):
	# if device is new create new object, set name and send new name to resolver
	if deviceUUID in uuidmap:
		d=uuidmap[deviceUUID]
	else:
		d=deviceInfo()
		d.name=deviceName
		setDeviceName(deviceUUID,deviceName)
	# update "Last seen" timestamp and device IP address
	d.lastseen=time.time()
	d.ip=deviceIP
	# store updated pickle
	uuidmap[deviceUUID]=d
	try:
		uuidmapfile = open("/etc/opt/agocontrol/jointspace/uuidmap.pck","w")
		pickle.dump(uuidmap, uuidmapfile, 0)
		uuidmapfile.close()
	except IOError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: Cannot update device store')

# Transmit new device name to resolver
def setDeviceName(deviceUUID, name):
	try:
		content = {}
		content["command"] = "setdevicename"
		content["uuid"] = deviceUUID
		content["name"] = name
		message = Message(content=content)
		sender.send(message)
	except SendError, e:
		print e

# Announce device to resolver
def reportDevice(deviceUUID, type, product):
	try:
		content = {}
		content["devicetype"]=type
		content["uuid"] = deviceUUID
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

# Report changed state to resolver
def sendStateChangedEvent(deviceUUID, level):
	try:
		content = {}
		content["uuid"] = deviceUUID
		content["level"] = level
		message = Message(content=content,subject="event.device.statechanged")
		sender.send(message)
	except SendError, e:
		print e

		
# broadcast discovery packet to LAN
def broadcast_discovery(frequency):
	buffer = pack('!32sii16s96s96s96s', 'Test', 0x01000000,0x02000000,myUUID.bytes,'Agocontrol-jointSpace','Agocontrol','Agocontrol')
	s = socket(AF_INET, SOCK_DGRAM)
	try:
		s.bind(('', 0))
	except ReceiverError, e:
		syslog.syslog(syslog.LOG_ERR, 'broadcast_discovery: failure to bind')
		s.close()
		raise	
	s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
	time.sleep(2)
	while True:
		s.sendto(buffer, ('<broadcast>', voodooPort))
		time.sleep(frequency)
	
# thread to listen for player info
def player_info():
	s = socket(AF_INET, SOCK_DGRAM)
	tempUUID=uuid
	try:
		s.bind(('', voodooPort))
	except ReceiverError, e:
		syslog.syslog(syslog.LOG_ERR, 'player_info: failure to bind')
		s.close()
		raise
	while True:
		d = s.recvfrom(1024)
		data = d[0]
		addr = d[1]
		message=unpack('!32sii16s96s96s96s', data)
		# extract data
		playerIP=addr[0]
		playerUUID=str(tempUUID.UUID(bytes=message[3]))
		playerUUID="dd9578f5-20bb-471b-b6ba-7df192b90166" # DEBUG
		playerName=message[4].strip('\0')
		playerVendor=message[5].strip('\0')
		playerModel=message[6].strip('\0')
		if playerUUID != str(myUUID):
			# log discovery
			log="Discovered - IP:"+playerIP \
				+", uuid:"+playerUUID \
				+", name:"+playerName \
				+", vendor:"+ playerVendor \
				+", model:"+ playerModel
			#print log # DEBUG
			syslog.syslog(syslog.LOG_NOTICE, log)
			# report to server and name device
			reportDevice(playerUUID, "avreceiver", playerModel)
			updateDevice(playerUUID, playerIP, playerName + " (" + playerVendor + " " + playerModel + ")")
		
syslog.syslog(syslog.LOG_NOTICE, "agocontrol jointspace device is starting up")

# read persistent uuid mapping from file
try:
	uuidmapfile = open("/etc/opt/agocontrol/jointspace/uuidmap.pck","r")
	uuidmap = pickle.load(uuidmapfile)
	uuidmapfile.close()
except IOError, e:
	uuidmap = {}

# Create player info collector thread
try:
	thread.start_new_thread( player_info, () )
except:
	syslog.syslog(syslog.LOG_ERR, 'Error: unable to start player info collector thread')
	raise

# Create discovery packet broadcast thread
try:
	thread.start_new_thread( broadcast_discovery, (10,) )
except:
	syslog.syslog(syslog.LOG_ERR, 'Error: unable to start discovery broadcast thread')
	raise

# exit the clean way on SIGINT
def signal_handler(signal, frame):
	#syslog.syslog(syslog.LOG_NOTICE, "agocontrol jointspace device is shutting down")
	# do some cleanup functions here
	#time.sleep(1)
	syslog.syslog(syslog.LOG_NOTICE, "agocontrol jointspace device has stopped")
	sys.exit(0)

# register signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

syslog.syslog(syslog.LOG_NOTICE, "agocontrol jointspace device is running")

# main loop
while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.content:
			if 'command' in message.content:
				#print message; #DEBUG
				# respond to broadcast commands
				if message.content['command'] == 'discover':
					syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
				elif message.content['command'] == 'inventory':
					syslog.syslog(syslog.LOG_NOTICE, "ignoring inventory command")
				# if not a broadcast command, check if command is for us
				else:
					# if message is for one of our childs, treat it
					if ('uuid' in message.content) and (message.content['uuid'] in uuidmap):
						#print "message is for one of our childs" # DEBUG
						deviceUUID=message.content['uuid']
						d=uuidmap[deviceUUID]
						# send ACK to acknowledge message reception if asked for
						if message.reply_to:
							replysender = session.sender(message.reply_to)
							response = Message("ACK")
							try:
								replysender.send(response)
							except SendError, e:
								print "Can't send ACK: ", e
							except NotFound, e:
								print "Can't send ACK: ", e
						command = ''
						if message.content['command'] == 'on':
							print d.name+" switched on" # DEBUG
							#result = set_outlet_state(path, 'on')
							#if "on" in result:
							sendStateChangedEvent(deviceUUID, 255)
						elif message.content['command'] == 'off':
							print d.name+" switched off" # DEBUG
							#result = set_outlet_state(path, 'off')
							#if "off" in result:
							sendStateChangedEvent(deviceUUID, 0)
					else:
						print "ignoring "+message.content['command']+" command" # DEBUG
	except Empty, e:
		pass
	except KeyError, e:
		print "key error in command evaluation", e
	except ReceiverError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: '+e)
		time.sleep(1)
