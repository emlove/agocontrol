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


def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "on":
			print "switching on port" + internalid
			mPowerDevice.SetDevice(internalid, 1)
			#client.emitEvent(internalid, "event.device.statechanged", "255", "")

		if content["command"] == "off":
			print "switching off port: " + internalid
			mPowerDevice.SetDevice(internalid, 0)
			#client.emitEvent(internalid, "event.device.statechanged", "0", "")

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
    	level = 0
	deviceState = dict()
        while (True):
			try:
				content = mPowerDevice.GetDevices()
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
				print "Website (%s) could not be reached due to %s" % (e.url, e.reason)
      
background = mPowerEvent()
background.setDaemon(True)
background.start()

client.run()

