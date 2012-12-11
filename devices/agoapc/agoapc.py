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

from fence_apc import *
from StringIO import StringIO

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

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
	apcusername = config.get("apc","username")
except:
	apcusername = "agocontrol"

try:
	apcpassword = config.get("apc","password")
except:
	apcpassword = "letmein"

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
	old_stdout = sys.stdout
	result = StringIO()
	sys.stdout = result

	options = {'-g': '20', '-F': '1', '-a': apchost, 'log': 0, '-C': ',', '-l': apcusername, '-o': 'list', '-G': '0', 'device_opt': ['help', 'version', 'agent', 'quiet', 'verbose', 'debug', 'action', 'ipaddr', 'login', 'passwd', 'passwd_script', 'secure', 'port', 'identity_file', 'switch', 'test', 'separator', 'inet4_only', 'inet6_only', 'ipport', 'power_timeout', 'shell_timeout', 'login_timeout', 'power_wait', 'retry_on', 'delay'], '-y': '5', '-u': 23, '-f': '0', '-p': apcpassword, '-c': '\n>', '-Y': '3', 'ssh_options': '-1 -c blowfish'}
	conn = fence_login(options)
	myresult = fence_action(conn, options, set_power_status, get_power_status, get_power_status)
	sys.stdout = old_stdout
	result_string = result.getvalue()
	apc_inventory = list(
    		line.strip().split(",") for line in result_string.split("\n") if line.strip()
	)
	apc_inventory.sort()

	devices = {}
	for index, item in apc_inventory:
		devices[lookupuuid(index)] = "switch"

	return(devices)

def sendcommand(path, command):
	old_stdout = sys.stdout
	result = StringIO()
	sys.stdout = result

	options = {'-g': '20', '-F': '1', '-a': apchost, 'log': 0, '-C': ',', '-l': apcusername, '-o': command, '-n': path, '-G': '0', 'device_opt': ['help', 'version', 'agent', 'quiet', 'verbose', 'debug', 'action', 'ipaddr', 'login', 'passwd', 'passwd_script', 'secure', 'port', 'identity_file', 'switch', 'test', 'separator', 'inet4_only', 'inet6_only', 'ipport', 'power_timeout', 'shell_timeout', 'login_timeout', 'power_wait', 'retry_on', 'delay'], '-y': '5', '-u': 23, '-f': '0', '-p': apcpassword, '-c': '\n>', '-Y': '3', 'ssh_options': '-1 -c blowfish'}

	conn = fence_login(options)
	myresult = fence_action(conn, options, set_power_status, get_power_status, get_power_status)

	# Redirect again the std output to screen
	sys.stdout = old_stdout

	# Then, get the stdout like a string and process it!
	result_string = result.getvalue()

	return(result_string)

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
		setDeviceName(newuuid, "apc: %s" % path)	
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
									result = sendcommand(path, 'on')
									if "Success: Powered ON" in result:
                                                                        	sendStateChangedEvent(uuid, 255)
                                                                if message.content['command'] == 'off':
                                                                        print "device switched off"
									result = sendcommand(path, 'off')
									if "Success: Powered OFF" in result:
                                                                        	sendStateChangedEvent(uuid, 0)
        except Empty, e:
                pass
        except KeyError, e:
                print "key error in command evaluation", e
        except ReceiverError, e:
                print e
                time.sleep(1)

