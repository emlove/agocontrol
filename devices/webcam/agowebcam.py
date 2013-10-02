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

			try:
				protocol, urldata = internalid.split("://")
				if "@" in  urldata:
					logindata, urlpart = urldata.split("@")
					username, password = logindata.split(":")
				else:
					urlpart = urldata
					username = ''
					password = ''

				url = protocol + "://" + urlpart				
				if password != '' and username != '':
					authmgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
					authmgr.add_password(None, url, username, password)
					handler = urllib2.HTTPBasicAuthHandler(authmgr)
					opener = urllib2.build_opener(handler)
					urllib2.install_opener(opener)
					u = urllib2.urlopen(url)
				else:
					u = urllib2.urlopen(url)	
			
				buffer = u.read()
				result["image"] = base64.b64encode(buffer)
				result["result"] = 0;

			except urllib2.URLError, e:
				print ('Error opening URL %s' % (url) + ' - Reason: ' + e.reason)

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
