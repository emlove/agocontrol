#
# ago control - UBNT mPower device
#
# copyright (c) 2013 Christoph Jaeger <office@diakonesis.at>
#

import agoclient
import threading
import time
import pyubnt



client = agoclient.AgoConnection("mPower")


def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "on":
			print "switching on port" + internalid
			mPowerDevice.SetDevice(internalid, 1)
			client.emitEvent(internalid, "event.device.statechanged", "255", "")

		if content["command"] == "off":
			print "switching off port: " + internalid
			mPowerDevice.SetDevice(internalid, 0)
			client.emitEvent(internalid, "event.device.statechanged", "0", "")

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
        while (True):
			time.sleep (5)
      
background = mPowerEvent()
background.setDaemon(True)
background.start()

client.run()

