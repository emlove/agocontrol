#
# ago control - UBNT mPower device
#
# copyright (c) 2013 Christoph Jaeger <office@diakonesis.at>
#

import agoclient
import threading
import time
import pyubnt

from urllib2 import URLError

client = agoclient.AgoConnection("mPower")

needs_connection = False

def messageHandler(internalid, content):
	global needs_connection
	if "command" in content:
		try:
		    if content["command"] == "on":
			    print "switching on port" + internalid
                            try:   
				mPowerDevice.SetDevice(internalid, 1)
			    except ValueError as e:
				needs_connection = True

		    if content["command"] == "off":
			    print "switching off port: " + internalid
                            try:   
				mPowerDevice.SetDevice(internalid, 0)
			    except ValueError as e:
				needs_connection = True

		except URLError as e:
				print "Device could not be reached due to %s" % (e.reason)
				print "Needs reconnect ..."
				needs_connection = True

# specify our message handler method
client.addHandler(messageHandler)


# get config parameters
host =  agoclient.getConfigOption("mPower", "host", "127.0.0.1")
username =  agoclient.getConfigOption("mPower", "username", "ubnt")
password = agoclient.getConfigOption("mPower", "password", "ubnt")

# initial call to mPower device
mPowerDevice = pyubnt.Device(host, username, password)

# add the devices of the mPower
content = mPowerDevice.GetDevices()
i = 1
for item in content["value"]:
        if "relay" in item:
		client.addDevice(str(i), "switch")
                i = i + 1

class mPowerEvent(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
	global needs_connection
	global content
	global mPowerDevice
	global host
	global username
	global password
    	level = 0
	deviceState = dict()
        while (True):
			try:
				if needs_connection:
					mPowerDevice = pyubnt.Device(host, username, password)
					needs_connection = False
				try:
					content = mPowerDevice.GetDevices()
				except ValueError as e:
					needs_connection = True
					continue
				x = 1
				for item in content["value"]:
					if "relay" in item:
							relayState = int(item["relay"])
							try:
								value = deviceState[x]
								if relayState != value:
									deviceState[x] = relayState
									print "state changed port %s to %s" % (x, relayState)
									if relayState == 1:
										relayState = 255
									stringRelayChanged = str(relayState)
									client.emitEvent(x, "event.device.statechanged", stringRelayChanged, "")

								
							except KeyError:
								deviceState[x] = relayState
							
							x = x + 1
				time.sleep (5)

			except URLError as e:
				print "Device could not be reached due to %s" % (e.reason)
      
background = mPowerEvent()
background.setDaemon(True)
background.start()

client.run()
