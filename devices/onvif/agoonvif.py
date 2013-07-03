#! /usr/bin/env python

import syslog

import agoclient

from WSDiscovery import *

client = agoclient.AgoConnection("onvif")

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "getvideoframe":
			print "nada"

client.addHandler(messageHandler)

# do a web service discovery to search for ONVIF NVTs
wsd = WSDiscovery()
wsd.start()

typeNVT = QName("http://www.onvif.org/ver10/network/wsdl","NetworkVideoTransmitter");

#ret = wsd.searchServices(scopes=[scope1], timeout=10)
ret = wsd.searchServices(types=[typeNVT])

for service in ret:
	print "Device: " + service.getEPR() + ":"
	print "Address information: " + str(service.getXAddrs())
	print "Scopes: " + str(service.getScopes())
	client.addDevice(service.getXAddrs()[0],"camera")

wsd.stop()

syslog.syslog(syslog.LOG_NOTICE, "agoonvif.py startup")
client.run()





