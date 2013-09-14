# This program is used to monitor when a wifi device joins/leaves the network
# and toggles a binary sensor based on  the device's state on the network
# This can be used to trigger events.  An example would be when a user's mobile phone
# connects then turn on lights.
#
# The code for this originated from https://github.com/blackairplane/pydetect
# but was heavily modified for use with Ago Control


import agoclient
import threading
import time
import os
import sys

# A list of the MAC addresses to monitor:
phoneaddress = ['00:00:00:00:00:00', 'ff:ff:ff:ff:ff:ff']

# Each device needs a name.  This should match the Ago Control device name you assign below
devicename = {'00:00:00:00:00:00': 'androidphone', 'ff:ff:ff:ff:ff:ff': 'iphone'}

client = agoclient.AgoConnection("Wifi_Device_Detect")
client.addDevice("androidphone", "binarysensor")
client.addDevice("iphone", "binarysensor")


def checkForDevice(deviceaddress):
        # See if the device has connected to the network
        systemCommand = "arp-scan -l | nawk '{print $2}' | grep -F -x '" + deviceaddress + "'"
        check_status = os.system(systemCommand) # Will return 0 if the line is found 256 if not found
	if check_status == 0:
		success = True
	else:
		success = False

        return success


def connectionDaemon(deviceaddress):
	connected = checkForDevice(deviceaddress)
	if (connected == True):
		#print devicename[deviceaddress] + " is online"  # Uncomment for debug
		client.emitEvent(devicename[deviceaddress], "event.device.statechanged", "255", "")
	else:
		#print devicename[deviceaddress] + " is offline" # Uncomment for debug
		client.emitEvent(devicename[deviceaddress], "event.device.statechanged", "0", "")


# This section is used to continually monitor devices joining/leaving the network

class wifi_detect_device(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
	i = 0
	while (i == 0):
		for deviceaddress in phoneaddress:
			connectionDaemon(deviceaddress)
		time.sleep(15)

 
background = wifi_detect_device()
background.setDaemon(True)
background.start()

client.run()

