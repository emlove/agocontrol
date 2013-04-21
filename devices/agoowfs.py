#! /usr/bin/env python

import sys
import syslog
import ow
import time
import pickle
import optparse
import ConfigParser

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
	username = config.get("system","username")
except:
	username = "agocontrol"

try:
	password = config.get("system","password")
except:
	password = "letmein"

try:
	broker = config.get("system","broker")
except:
	broker = "localhost"

try:
	device = config.get("owfs","device")
except:
	device = "/dev/ttyUSB0"

try:
	debug = config.get("system","debug")
except:
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
parser.add_option("-d", "--device", default=device, help="serial device for owfs")

opts, args = parser.parse_args()

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

# read persistent uuid mapping from file
try:
	uuidmapfile = open("/etc/opt/agocontrol/owfs/uuidmap.pck","r")
	uuidmap = pickle.load(uuidmapfile)
	uuidmapfile.close()
except IOError, e:
	uuidmap = {}

sensors = {}

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

def lookupuuid(path):
	if path in uuidmap:
		pass
	else:
		newuuid = str(uuid4())
		uuidmap[path] = newuuid
		try:
			# uuid is new, try to store it
			uuidmapfile = open("/etc/opt/agocontrol/owfs/uuidmap.pck","w")
			pickle.dump(uuidmap, uuidmapfile)
			uuidmapfile.close()
		except IOError, e:
			pass
	return uuidmap[path]

def sendlightevent(path, light):
	try:
		content = {}
		content["uuid"] = lookupuuid(path)
		content["level"] = light
		content["unit"] = "percent"
		message = Message(content=content,subject="event.environment.brightnesschanged")
		sender.send(message)
	except SendError, e:
		print e

def sendhumevent(path, hum):
	try:
		content = {}
		content["uuid"] = lookupuuid(path)
		content["level"] = hum
		content["unit"] = "percent"
		message = Message(content=content,subject="event.environment.humiditychanged")
		sender.send(message)
	except SendError, e:
		print e

def sendtempevent(path, temp):
	try:
		content = {}
		content["uuid"] = lookupuuid(path)
		content["level"] = float(temp)
		content["unit"] = "degC"
		message = Message(content=content,subject="event.environment.temperaturechanged")
		sender.send(message)
	except SendError, e:
		print e

def sendSensorTriggerEvent(path, level):
	try:
		content = {}
		content["uuid"] = lookupuuid(path)
		content["level"] = level
		message = Message(content=content,subject="event.security.sensortriggered")
		sender.send(message)
	except SendError, e:
		print e

def reportdevice(path, type='multilevelsensor', product='1wire device'):
	try:
		content = {}
		content["devicetype"]=type
		content["event"] = "announce"
		content["uuid"] = lookupuuid(path)
		content["internal-id"] = path
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

syslog.syslog(syslog.LOG_NOTICE, "agoowfs.py startup")
ow.init( opts.device )

syslog.syslog(syslog.LOG_NOTICE, "reading devices")
root = ow.Sensor( '/' )

startup = True

counter = 4
while True:
	counter=counter+1
	if counter==5:
		counter = 0
		try:
			for sensor in root.sensors():
				if sensor._type == 'DS18S20' or sensor._type == 'DS18B20' or sensor._type == 'DS2438':
					if startup:
						reportdevice(sensor._path)
					temp = round(float(sensor.temperature),1)
					if sensor._path in sensors:
						if 'temp' in sensors[sensor._path]:
							if abs(sensors[sensor._path]['temp'] - temp) > 0.2:
								sendtempevent( sensor._path, temp)
								sensors[sensor._path]['temp'] = temp
					else:
						sendtempevent( sensor._path, temp)
						sensors[sensor._path]={}
						sensors[sensor._path]['temp'] = temp
				if sensor._type == 'DS2438':
					try:
						if ow.owfs_get('%s/MultiSensor/type' % sensor._path) == 'MS-TL':
							rawvalue = float(ow.owfs_get('/uncached%s/VAD' % sensor._path ))
							if rawvalue > 10:
								rawvalue = 0
							lightlevel = int(round(20*rawvalue))
							if 'light' in sensors[sensor._path]:
								if abs(sensors[sensor._path]['light'] - lightlevel) > 2:
									sendlightevent( sensor._path, lightlevel)
									sensors[sensor._path]['light'] = lightlevel
							else:
								sendlightevent( sensor._path, lightlevel)
								sensors[sensor._path]['light'] = lightlevel
						if ow.owfs_get('%s/MultiSensor/type' % sensor._path) == 'MS-TH':
							
							humraw = ow.owfs_get('/uncached%s/humidity' % sensor._path )
							humidity = round(float(humraw))
							if 'hum' in sensors[sensor._path]:
								if abs(sensors[sensor._path]['hum'] - humidity) > 1:
									sendhumevent( sensor._path, humidity)
									sensors[sensor._path]['hum'] = humidity
							else:
								sendhumevent( sensor._path, humidity)
								sensors[sensor._path]['hum'] = humidity
					except ow.exUnknownSensor, e:
						print e
				if sensor._type == 'DS2406':
					if startup:
						# print sensor.entryList()
						sensor.PIO_A = '0'
						sensor.latch_A = '0'
						sensor.set_alarm = '111'
					if sensor.latch_A == '1':
						sensor.latch_A = '0'
						sendSensorTriggerEvent(sensor._path, sensor.sensed_A)
			startup = False
		except ow.exUnknownSensor, e:
			pass
		try:
			message = receiver.fetch(timeout=3)
			if message.content:
				if 'command' in message.content:
					if message.content['command'] == 'discover':
						syslog.syslog(syslog.LOG_NOTICE, "device discovery")
						for path in sensors.iterkeys():
							reportdevice(path)
		except Empty, e:
			pass
		except ReceiverError, e:
			print e
			time.sleep(1)

