#!/usr/bin/python

# ago client webcam device
#
# copyright (c) 2013 Harald Klein <hari+ago@vt100.at>
#

import agoclient
import urllib2
import base64

client = agoclient.AgoConnection("webcam")


def messageHandler(internalid, content):
	result = {}
	result["result"] = -1;
	if "command" in content:
		if content['command'] == 'getvideoframe':
			print "getting video frame"
			u = urllib2.urlopen(internalid)	
			buffer = u.read()
			result["image"] = base64.b64encode(buffer)
			result["result"] = 0;
	return result

client.addHandler(messageHandler)
devicelist=agoclient.getConfigOption("webcam", "devices", "")

try:
	devices = map(str, devicelist.split(','))
except:
	print "error reading device list"
else:
	for device in devices:
		print "announcing device", device
		if "rtsp://" in device:
			client.addDevice(device, "onvifnvt")
		else:
			client.addDevice(device, "camera")

client.run()
