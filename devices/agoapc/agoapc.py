#! /usr/bin/env python
# APC Switched Rack PDU Device

import sys
import syslog
import pickle
import optparse
import ConfigParser
import socket

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto import rfc1902

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')


OIDOutletCount = "1,3,6,1,4,1,318,1,1,4,5,1,0"	# sPDUOutletConfigTableSize
OIDStatus = "1,3,6,1,4,1,318,1,1,4,4,2,1,3"	# sPDUOutletCtl
OIDName = "1,3,6,1,4,1,318,1,1,4,5,2,1,3"	# sPDUOutletName
OIDLoad = "1,3,6,1,4,1,3181,1,12,2,3,1,1,2,1"	# rPDULoadStatusLoad


try:
	username = config.get("system","username")
except ConfigParser.NoOptionError, e:
	username = "agocontrol"

try:
	password = config.get("system","password")
except ConfigParser.NoOptionError, e:
	password = "letmein"

try:
	broker = config.get("system","broker")
except ConfigParser.NoOptionError, e:
	broker = "localhost"

try:
	debug = config.get("system","debug")
except ConfigParser.NoOptionError, e:
	debug = "WARN"

try:
	apchost = config.get("apc","host")
except:
	apchost = "localhost"

try:
	apcport = int(config.get("apc","port"))
except:
	apcport = 161

try:
	apccommunityro = config.get("apc","community_readonly")
except:
	apccommunityro= "public"

try:
	apccommunityrw = config.get("apc","community_readwrite")
except:
	apccommunityrw = "private"

if debug=="DEBUG":
	enable("qpid", DEBUG)
else:
	enable("qpid", WARN)

 
parser = optparse.OptionParser(usage="usage: %prog <command> [options] [ PARAMETERS ... ]",
                               description="send automation control commands")
parser.add_option("-b", "--broker", default=broker, help="hostname of broker (default %default)")
parser.add_option("-u", "--username", default=username, help="specify a username")
parser.add_option("-P", "--password", default=password, help="specify a password")

opts, args = parser.parse_args()

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()


# read persistent uuid mapping from file
try:
        uuidmapfile = open("/etc/opt/agocontrol/apc/uuidmap.pck","r")
        uuidmap = pickle.load(uuidmapfile)
        uuidmapfile.close()
except IOError, e:
        uuidmap = {}


connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")



def inventory():
	# get outlets from apc 
	myoid = eval(str(OIDOutletCount))
	__errorIndication, __errorStatus, __errorIndex, varBinds = cmdgen.CommandGenerator().getCmd(
		cmdgen.CommunityData('my-agent', 'public', 0),
		cmdgen.UdpTransportTarget((apchost, apcport)),
		myoid )

	outletCount = varBinds[0][1]
	
	devices = {}

	for outlet in range(1,outletCount+1):
		devices[lookupuuid(outlet)] = "switch"

	return(devices)


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


# read persistent uuid mapping from file
try:
        uuidmapfile = open("/etc/opt/agocontrol/apc/uuidmap.pck","r")
        uuidmap = pickle.load(uuidmapfile)
        uuidmapfile.close()
except IOError, e:
        uuidmap = {}

def setDeviceName(uuid, name):
        try:
                content = {}
                content["command"] = "setdevicename"
                content["uuid"] = uuid
                content["name"] = name
		message = Message(content=content)
                sender.send(message)
        except SendError, e:
                print e


def lookupuuid(path):
        if path in uuidmap:
                pass
        else:
                newuuid = str(uuid4())
                uuidmap[path] = newuuid
		outlet_name = get_outlet_name(path)
		if outlet_name == "":
			setDeviceName(newuuid, "APC: %s" % path)
		else:
			setDeviceName(newuuid, "APC: %s" % outlet_name)	

                try:
                        # uuid is new, try to store it
                        uuidmapfile = open("/etc/opt/agocontrol/apc/uuidmap.pck","w")
                        pickle.dump(uuidmap, uuidmapfile)
                        uuidmapfile.close()
                except IOError, e:
                        pass
        return uuidmap[path]


def reportdevice(uuid='a8ee399e-16f3-4ea4-9cc5-16aa9cd7aed2', type='switch', product='ago control APC device'):
	try:
		content = {}
		content["devicetype"]=type
		content["uuid"] = uuid
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

def sendStateChangedEvent(uuid, level):
        try:
                content = {}
                content["uuid"] = uuid
                content["level"] = level
                message = Message(content=content,subject="event.device.statechanged")
                sender.send(message)
        except SendError, e:
                print e

syslog.syslog(syslog.LOG_NOTICE, "agoapc.py startup")

devices=inventory()

def discovery():
	for (uuid, devicetype) in devices.iteritems():
		reportdevice(uuid=uuid, type=devicetype)

	for (path, uuid) in uuidmap.iteritems():
		result = get_outlet_status(path)
		if "on" in result:
        	       	sendStateChangedEvent(uuid, 255)
		if "off" in result:
                	sendStateChangedEvent(uuid, 0)



discovery()


startup = True

while True:
        try:
                message = receiver.fetch(timeout=1)
                if message.content:
                        if 'command' in message.content:
                                print message
                                if message.content['command'] == 'discover':
                                        syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
                                        discovery()
                                elif message.content['command'] == 'inventory':
                                        syslog.syslog(syslog.LOG_NOTICE, "ignoring inventory command")
                                else:
                                        if 'uuid' in message.content:
                                                for (path, uuid) in uuidmap.iteritems():
                                                        if message.content['uuid'] == uuid:
                                                                # send reply
                                                                if message.reply_to:
                                                                        replysender = session.sender(message.reply_to)
                                                                        response = Message("ACK")
                                                                        try:
                                                                                replysender.send(response)
                                                                        except SendError, e:
                                                                                print "Can't send ACK: ", e
                                                                        except NotFound, e:
                                                                                print "Can't send ACK: ", e
                                                                # print path, uuid
                                                                command = ''
                                                                if message.content['command'] == 'on':
                                                                        print "device switched on"
                                                                        result = set_outlet_state(path, 'on')
                                                                        if "on" in result:
                                                                                sendStateChangedEvent(uuid, 255)
                                                                if message.content['command'] == 'off':
                                                                        print "device switched off"
                                                                        result = set_outlet_state(path, 'off')
                                                                        if "off" in result:
                                                                                sendStateChangedEvent(uuid, 0)
        except Empty, e:
                pass
        except KeyError, e:
                print "key error in command evaluation", e
        except ReceiverError, e:
                print e
                time.sleep(1)

