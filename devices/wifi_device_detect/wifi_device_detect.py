# This program is used to monitor when a wifi device joins/leaves the network
# and toggles a binary sensor based on  the device's state on the network
# This can be used to trigger events.  An example would be when a user's mobile phone
# connects then turn on lights.
#
# The code for this originated from https://github.com/blackairplane/pydetect
# but was heavily modified for use with Ago Control
# 
# Create /etc/opt/agocontrol/conf.d/wifi_device_detect.conf
# [wifi_device_detect]
# phoneaddress=AA:00:BB:11:CC:22,33:DD:44:EE:55:FF
# devicename=androidphone,iphone
# wait_time=15
# check_time=15
#
# *NOTE*  First phone address (MAC Address) matches first devicename, second matches second, etc
#         wait_time is the maximum time (minutes) a device can be inactive before being marked as away
#         check_time is the time (seconds) between each check 		


import agoclient
import threading
import time
import os
import sys

readPhoneaddress = agoclient.getConfigOption("wifi_device_detect","phoneaddress","00:00:00:00:00:00, FF:FF:FF:FF:FF:FF")
phoneaddress = map(str, readPhoneaddress.split(','))

readDevicename = agoclient.getConfigOption("wifi_device_detect","devicename","androidphone, iphone")
devicename =  map(str, readDevicename.split(','))

client = agoclient.AgoConnection("Wifi_Device_Detect")
for name in devicename:
	client.addDevice(name, "binarysensor")

wifidevices = dict(zip(phoneaddress, devicename))

last_seen = {}
for address in phoneaddress:
	last_seen[address] = 0

wait_time = float(agoclient.getConfigOption("wifi_device_detect","wait_time","15"))
check_time = float(agoclient.getConfigOption("wifi_device_detect","check_time","15"))


def checkForDevice(deviceaddress):
        # See if the device has connected to the network
        systemCommand = "arp-scan -l | nawk '{print $2}' | grep -i -F -x '" + deviceaddress + "'"
        check_status = os.system(systemCommand) # Will return 0 if the line is found 256 if not found
	if check_status == 0:
		last_seen[deviceaddress] = time.time();
		success = True
	else:
		checktime = time.time() - float(last_seen[deviceaddress])
		if (checktime > (wait_time * 60)):
			success = False
			#print "False"
			#print (checktime/60)
		else:
			success = "Undetermined"
			#print "Undetermined"
			#print (checktime/60)

        return success


def connectionDaemon(deviceaddress):
	connected = checkForDevice(deviceaddress)
	if (connected == True):
		#print wifidevices[deviceaddress] + " is online"  # Uncomment for debug
		client.emitEvent(wifidevices[deviceaddress], "event.device.statechanged", "255", "")
	if (connected == False):
		#print wifidevices[deviceaddress] + " is offline" # Uncomment for debug
		client.emitEvent(wifidevices[deviceaddress], "event.device.statechanged", "0", "")

def initDevices():
	for deviceaddress in phoneaddress:
		last_seen[deviceaddress] = time.time();	
		client.emitEvent(wifidevices[deviceaddress], "event.device.statechanged", "0", "")


class wifi_detect_device(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
	initDevices()
	i = 0
	while (i == 0):
		for deviceaddress in phoneaddress:
			connectionDaemon(deviceaddress)
		time.sleep(check_time)

 
background = wifi_detect_device()
background.setDaemon(True)
background.start()

client.run()

