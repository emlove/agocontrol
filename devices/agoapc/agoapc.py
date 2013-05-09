#! /usr/bin/env python
# APC Switched Rack PDU Device

import sys
import syslog
import socket

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902
import thread
import time

import agoclient

client = agoclient.AgoConnection("apc")

OIDOutletCount = "1,3,6,1,4,1,318,1,1,4,5,1,0"	# sPDUOutletConfigTableSize
OIDStatus = "1,3,6,1,4,1,318,1,1,4,4,2,1,3"	# sPDUOutletCtl
OIDName = "1,3,6,1,4,1,318,1,1,4,5,2,1,3"	# sPDUOutletName
OIDLoad = "1,3,6,1,4,1,318,1,1,12,2,3,1,1,2,1"	# rPDULoadStatusLoad
loadOID = (1,3,6,1,4,1,318,1,1,12,2,3,1,1,2,1)

apchost = agoclient.getConfigOption("apc", "host", "192.168.80.3")
apcport = int(agoclient.getConfigOption("apc", "port", "161") ) 
apcvoltage = int(agoclient.getConfigOption("apc", "voltage", "220") ) 
apccommunityro =  agoclient.getConfigOption("apc", "community_readonly", "public")
apccommunityrw =  agoclient.getConfigOption("apc", "community_readwrite", "private")

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()


# get outlets from apc 
myoid = eval(str(OIDOutletCount))
__errorIndication, __errorStatus, __errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
	cmdgen.CommunityData('my-agent', 'public', 0),
	cmdgen.UdpTransportTarget((apchost, apcport)),
	myoid )

outletCount = varBinds[0][1]

for outlet in range(1,outletCount+1):
	client.addDevice(outlet, "switch")


def set_outlet_state(path, command):
	#new_state = 1 # 1=enable; 2=disable
	if "on" in command:
		new_state = 1
	else:
		new_state = 2

	myoid = eval(str(OIDStatus) + "," + str(path))
	__errorIndication, __errorStatus, __errorIndex, __varBinds = cmdgen.CommandGenerator().setCmd(
		cmdgen.CommunityData('my-agent', 'private', 1),
		cmdgen.UdpTransportTarget((apchost, apcport)),
		(myoid, rfc1902.Integer(new_state)))
	
	status = get_outlet_status(path)
	return(status)


def get_outlet_status(path):

	myoid = eval(str(OIDStatus) + "," + str(path))
	__errorIndication, __errorStatus, __errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
		cmdgen.CommunityData('my-agent', 'public', 0),
		cmdgen.UdpTransportTarget((apchost, apcport)), myoid)
	output = varBinds[0][1]

	if output == 1:
		status = "on"
	if output == 2:
		status = "off"
	if output == 4:
		status = "unknown"

        return(status)

def get_outlet_name(path):

	myoid = eval(str(OIDName) + "," + str(path))
	__errorIndication, __errorStatus, __errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
		cmdgen.CommunityData('my-agent', 'public', 0),
		cmdgen.UdpTransportTarget((apchost, apcport)), myoid)
	output = varBinds[0][1]

        return(output)

def get_current_power():

	myoid = eval(str(OIDLoad))
	errorIndication, errorStatus, errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
    		cmdgen.CommunityData('my-agent', 'public', 0),
    		cmdgen.UdpTransportTarget((apchost, apcport)),
    		myoid
		)
	myload = varBinds[0][1]

	if myload == "-1":
        	return int(-1)
	result = float(float(int(myload)) / 10)

	return(result)


# thread to poll energy level
def print_time( threadName, delay):
	old_currentPower = 0
	unit = "Wh"
	while True:
		try:
			time.sleep(delay)
			currentPowerA = get_current_power()
			currentPower = int(float(currentPowerA * apcvoltage))
			if currentPower != old_currentPower:
				# client.emitEvent(threadname, "event.environment.powerusage", currentPower, unit)
				print "%s: %s" % ( threadName, currentPower ) 
				old_currentPower = currentPower

		except:
			time.sleep(1)

# Create Energy-Level thread
#try:
#	thread.start_new_thread( print_time, ("Energy-Level:", 10, ) )
#except:
#	print "Error: unable to start thread"


syslog.syslog(syslog.LOG_NOTICE, "agoapc.py startup")

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "on":
			print "device switched on: ", internalid
			result = set_outlet_state(internalid, 'on')
			if "on" in result:
				client.emitEvent(internalid, "event.device.statechanged", "255", "")
		if content["command"] == "off":
			print "device switched off:", internalid
			result = set_outlet_state(path, 'off')
			if "off" in result:
				client.emitEvent(internalid, "event.device.statechanged", "0", "")

client.addHandler(messageHandler)

client.run()

