#! /usr/bin/env python

import sys
import syslog
import ow
import time
import threading

import agoclient

client = agoclient.AgoConnection("owfs")

device = agoclient.getConfigOption("owfs", "device", "/dev/usbowfs")

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

sensors = {}

syslog.syslog(syslog.LOG_NOTICE, "agoowfs.py startup")
try:
	ow.init( device )
except ow.exNoController:
	syslog.syslog(syslog.LOG_ERROR, "can't open one wire device, aborting")
	time.sleep(5)
	exit(-1)

syslog.syslog(syslog.LOG_NOTICE, "reading devices")
root = ow.Sensor( '/' )


for sensor in root.sensors():
	if sensor._type == 'DS18S20' or sensor._type == 'DS18B20':
		client.addDevice(sensor._path, "multilevelsensor");
	if sensor._type == 'DS2438':
		try:
			if ow.owfs_get('%s/MultiSensor/type' % sensor._path) == 'MS-TL':
				client.addDevice(sensor._path, "multilevelsensor");
			if ow.owfs_get('%s/MultiSensor/type' % sensor._path) == 'MS-TH':
				client.addDevice(sensor._path, "multilevelsensor");
		except ow.exUnknownSensor, e:
			print e
	if sensor._type == 'DS2406':
		sensor.PIO_B = '0'
		sensor.latch_B = '0'
		sensor.set_alarm = '111'
		client.addDevice(sensor._path, "switch");
		client.addDevice(sensor._path, "binarysensor");

def messageHandler(internalid, content):
	for sensor in root.sensors():
		if (sensor._path == intenralid):
			if "command" in content:
				if content["command"] == "on":
					print "switching on: ", internalid
					sensor.PIO_A = '1'
					client.emitEvent(internalid, "event.device.state", "255", "")
				if content["command"] == "off":
					print "switching off: ", internalid
					sensor.PIO_A = '0'
					client.emitEvent(internalid, "event.device.state", "0", "")

client.addHandler(messageHandler)
					
class readBus(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
	# wait till devices should be announced
	time.sleep(5)
        while (True):
		try:
			for sensor in root.sensors():
				if sensor._type == 'DS18S20' or sensor._type == 'DS18B20' or sensor._type == 'DS2438':
					temp = round(float(sensor.temperature),1)
					if sensor._path in sensors:
						if 'temp' in sensors[sensor._path]:
							if abs(sensors[sensor._path]['temp'] - temp) > 0.5:
								client.emitEvent( sensor._path, "event.environment.temperaturechanged", temp, "degC")
								sensors[sensor._path]['temp'] = temp
					else:
						client.emitEvent( sensor._path, "event.environment.temperaturechanged", temp, "degC")
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
								if abs(sensors[sensor._path]['light'] - lightlevel) > 5:
									client.emitEvent( sensor._path, "event.environment.brightnesschanged", lightlevel, "percent")
									sensors[sensor._path]['light'] = lightlevel
							else:
								client.emitEvent( sensor._path, "event.environment.brightnesschanged", lightlevel, "percent")
								sensors[sensor._path]['light'] = lightlevel
						if ow.owfs_get('%s/MultiSensor/type' % sensor._path) == 'MS-TH':
							
							humraw = ow.owfs_get('/uncached%s/humidity' % sensor._path )
							humidity = round(float(humraw))
							if 'hum' in sensors[sensor._path]:
								if abs(sensors[sensor._path]['hum'] - humidity) > 2:
									client.emitEvent( sensor._path, "event.environment.humiditychanged", humidity, "percent")
									sensors[sensor._path]['hum'] = humidity
							else:
								client.emitEvent( sensor._path, "event.environment.humiditychanged", humidity, "percent")
								sensors[sensor._path]['hum'] = humidity
					except ow.exUnknownSensor, e:
						print e
				if sensor._type == 'DS2406':
					if sensor.latch_B == '1':
						sensor.latch_B = '0'
						sendSensorTriggerEvent(sensor._path, sensor.sensed_B)
		except ow.exUnknownSensor, e:
			pass
		time.sleep(2)
      
background = readBus()
background.setDaemon(True)
syslog.syslog(syslog.LOG_NOTICE, "starting readBus() thread")
background.start()

syslog.syslog(syslog.LOG_NOTICE, "passing control to agoclient")
client.run()
