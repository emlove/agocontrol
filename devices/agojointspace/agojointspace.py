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
	jointspaceport = int(config.get("jointspace","port"))
except:
	jointspaceport = 1925

try:
	voodooPort = int(config.get("jointspace","voodooport"))
except:
	voodooPort = 2323

try:
	deviceTimeout = int(config.get("jointspace","timeout"))
except:
	deviceTimeout = 65

if debug=="DEBUG":
	enable("qpid", DEBUG)
else:
	enable("qpid", WARN)

 
parser = optparse.OptionParser(usage="usage: %prog <command> [options] [ PARAMETERS ... ]", description="send automation control commands")
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

connection = Connection(opts.broker, username=opts.username, password=opts.password, reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

###
### LOCAL PERSISTENT DEVICE INFO STORE
###

# Update store (pickle file)
def updateStore():
	try:
		uuidmapfile = open("/etc/opt/agocontrol/jointspace/uuidmap.pck","w")
		pickle.dump(uuidmap, uuidmapfile, 0)
		uuidmapfile.close()
	except IOError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: Cannot update device store')

# Update device name, ip address and lastseen timestamp
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
	if not get_device_volume(d):
		syslog.syslog(syslog.LOG_ERR, 'Error getting volume from ' + d.name)
	# store updated pickle
	uuidmap[deviceUUID]=d
	updateStore()

###
### COMMUNICATION WITH RESOLVER
###

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
		syslog.syslog(syslog.LOG_ERR, 'Error: (setDeviceName) ' + e)

###
### EVENTS TO REPORT BACK TO RESOLVER
###

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
		syslog.syslog(syslog.LOG_ERR, 'Error: (reportDevice) ' + e)

# Remove device from resolver
def removeDevice(deviceUUID):
	syslog.syslog(syslog.LOG_NOTICE, "Removing " + uuidmap[deviceUUID].name + " from resolver")
	try:
		content = {}
		content["uuid"] = deviceUUID
		message = Message(content=content,subject="event.device.remove")
		sender.send(message)
	except SendError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: (removeDevice) ' + e)

# Report changed state to resolver
def sendStateChangedEvent(deviceUUID, level):
	try:
		content = {}
		content["uuid"] = deviceUUID
		content["level"] = level
		message = Message(content=content,subject="event.device.statechanged")
		sender.send(message)
	except SendError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: (sendStateChangedEvent) ' + e)

# Report changed device volume to resolver
def sendVolumeChangedEvent(deviceUUID, level):
	try:
		content = {}
		content["uuid"] = deviceUUID
		content["level"] = level
		message = Message(content=content,subject="event.device.volumechanged")
		#sender.send(message)
		syslog.syslog(syslog.LOG_NOTICE, "Volume changed event not yet available on core")
	except SendError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: '+e)

# Report changed device channel to resolver
def sendChannelChangedEvent(deviceUUID, channel):
	try:
		content = {}
		content["uuid"] = deviceUUID
		content["channel"] = channel
		message = Message(content=content,subject="event.device.channelchanged")
		#sender.send(message)
		syslog.syslog(syslog.LOG_NOTICE, "Channel changed event not yet available on core")
	except SendError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: '+e)

# Scan through device list and remove devices not seen for a specified period of time
def scanDeviceTimeouts():
    for deviceUUID, device in uuidmap.items():
		if (time.time() - device.lastseen > deviceTimeout):
			removeDevice(deviceUUID)
			del uuidmap[deviceUUID]
			updateStore()

###
### DIRECTFB / VOODOO PLAYER DISCOVERY
### used to discover jointspace capable devices on LAN
###

# broadcast discovery packet to LAN
def broadcast_discovery(frequency):
	buffer = pack('!32sii16s96s96s96s', 'V1.0', 0x01000000,0x02000000,myUUID.bytes,'Agocontrol-jointSpace','Agocontrol','Agocontrol')
	s = socket(AF_INET, SOCK_DGRAM)
	try:
		s.bind(('', 0))
	except ReceiverError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: Failure to bind (broadcast_discovery)')
		s.close()
		raise	
	s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
	time.sleep(2)
	while True:
		scanDeviceTimeouts()
		s.sendto(buffer, ('<broadcast>', voodooPort))
		time.sleep(frequency)
	
# thread to listen for player info
def player_info():
	s = socket(AF_INET, SOCK_DGRAM)
	tempUUID=uuid
	try:
		s.bind(('', voodooPort))
	except ReceiverError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: Failure to bind (player_info)')
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
		#playerUUID="dd9578f5-20bb-471b-b6ba-7df192b90166" # DEBUG
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
			syslog.syslog(syslog.LOG_NOTICE, log)
			# report to server and name device
			reportDevice(playerUUID, "tv", playerModel)
			updateDevice(playerUUID, playerIP, playerName + " (" + playerVendor + " " + playerModel + ")")

###
### JOITSPACE REST API COMMUNICATION
###

# post json data to jointspace REST API
def post_json(device, json, path):
	print "JSON: "+json #DEBUG
	url = "http://"+device.ip+":"+str(jointspaceport)+path
	try:
		req = urllib2.Request(url, json, {'Content-Type': 'application/json'})
		f = urllib2.urlopen(req)
		response = f.read()
		print response # DEBUG
	except urllib2.URLError,e:
		syslog.syslog(syslog.LOG_ERR, 'Error: ' + str(e.reason))
		return False
	except:
		return False
	else:
		f.close()
		return True

# simulate a TV remote key press 
def send_key(device,key):
	return post_json(device, json.dumps({'key': key}),"/1/input/key")
		
# set device power state
def set_device_power(device,state):
	if state == 'off':
		syslog.syslog(syslog.LOG_NOTICE, 'Powering off ' + device.name)
		if send_key(device,'Standby'):
			return True
		else:
			return False
	elif state == 'on':
		syslog.syslog(syslog.LOG_NOTICE, 'Powering on ' + device.name)
		syslog.syslog(syslog.LOG_ERR, 'Error:  power on currently not supported')
		return False
	else:
		syslog.syslog(syslog.LOG_ERR, 'Error: (set_device_power) State ' + state + " unknown")
		return False

# set device volume and mute state
def set_device_volume(device,volume):
	if volume == '+':
		if send_key(device,'VolumeUp'):
			return True
		else:
			return False
	elif volume == '-':
		if send_key(device,'VolumeDown'):
			return True
		else:
			return False
	elif volume == 'mute':
		data = {'muted': True}
		return post_json(device, json.dumps(data),"/1/audio/volume")
	else:
		data = {'current': int(volume) * device.volume_max / 100}
		if post_json(device, json.dumps(data),"/1/audio/volume"):
			device.volume_current = int(volume)
			updateStore()
			return True
		else:
			return False

# get device volume, mute state and minimum / maximum possible volume values
def get_device_volume(device):
	url = "http://" + device.ip + ":" + str(jointspaceport) + "/1/audio/volume"
	try:
		data = json.load(urllib2.urlopen(url))
		device.volume_min = int(data['min'])
		device.volume_max = int(data['max'])
		device.volume_muted = data['muted']
		device.volume_current = int(data['current'])
		return True
	except:
		return False

# set device channel
def set_device_channel(device,channel):
	if channel == '+':
		if send_key(device,'ChannelStepUp'):
			return True
		else:
			return False
	elif channel == '-':
		if send_key(device,'ChannelStepDown'):
			return True
		else:
			return False
	else:
		data = {'id': channel}
		if post_json(device, json.dumps(data),"/1/channels/current"):
			device.channel_current = int(channel)
			updateStore()
			return True
		else:
			return False

###
### MAIN WORKING SPAGHETTI
###
	
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
	thread.start_new_thread( broadcast_discovery, (30,) )
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
						#pprint(message.content) # DEBUG
						deviceUUID=message.content['uuid']
						d=uuidmap[deviceUUID]
						# send ACK to acknowledge message reception if asked for
						if message.reply_to:
							replysender = session.sender(message.reply_to)
							response = Message("ACK")
							try:
								replysender.send(response)
							except SendError, e:
								syslog.syslog(syslog.LOG_ERR, "Error: Can't send ACK: ", e)

							except NotFound, e:
								syslog.syslog(syslog.LOG_ERR, "Error: Can't send ACK: ", e)
						command = ''
						
						# Power ON
						if message.content['command'] == 'on':
							if set_device_power(d, 'on'):
								sendStateChangedEvent(deviceUUID, 100)
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error executing the power on command for '+d.name)
						
						# Power OFF
						elif message.content['command'] == 'off':
							if set_device_power(d, 'off'):
								sendStateChangedEvent(deviceUUID, 0)
								removeDevice(deviceUUID)
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error executing the power off command for '+d.name)
						
						# Volume +
						elif message.content['command'] == 'vol+':
							if set_device_volume(d, '+'):
								# send new volume to resolver here
								pass 
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error executing the vol+ command for '+d.name)
						
						# Volume -
						elif message.content['command'] == 'vol-':
							if set_device_volume(d, '-'):
								# send new volume to resolver here
								pass 
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error executing the vol- command for '+d.name)
						
						# set volume level
						elif (message.content['command'] == 'setlevel') and ('level' in message.content):
							if set_device_volume(d, message.content['level']):
								syslog.syslog(syslog.LOG_NOTICE, d.name + " changed volume to " + str(d.volume_current))
								# send new volume to resolver here
								sendVolumeChangedEvent(deviceUUID, d.volume_current / d.volume_max * 100)
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error setting the volume for '+d.name)
						# Channel +
						elif message.content['command'] == 'chan+':
							if set_device_channel(d, '+'):
								# send new channel to resolver here
								pass 
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error executing the channel+ command for '+d.name)
						
						# Channel -
						elif message.content['command'] == 'chan-':
							if set_device_channel(d, '-'):
								# send new channel to resolver here
								pass 
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error executing the channel- command for '+d.name)
						
						# set channel number
						elif (message.content['command'] == 'setchannel') and ('channel' in message.content):
							if set_device_channel(d, message.content['channel']):
								# send new channel to resolver here
								sendChannelChangedEvent(deviceUUID, d.channel_current)
							else:
								syslog.syslog(syslog.LOG_ERR, 'Error setting the channel for '+d.name)
					else:
						#print "ignoring "+message.content['command']+" command" # DEBUG
						pass
	except Empty, e:
		pass
	except KeyError, e:
		syslog.syslog(syslog.LOG_ERR, "Error:  Key error in command evaluation", e)
	except ReceiverError, e:
		syslog.syslog(syslog.LOG_ERR, 'Error: '+e)
		time.sleep(1)
