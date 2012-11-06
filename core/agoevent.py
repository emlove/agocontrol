#! /usr/bin/env python

import sys
import syslog
import time
import pickle
import optparse
import ConfigParser
from boolParser import BoolParser

from array import array

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

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
	eventmapfile = open("/etc/opt/agocontrol/events.pck","r")
	eventmap = pickle.load(eventmapfile)
	eventmapfile.close()
except IOError, e:
	eventmap = {}

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

def savemap():
	try:
		eventmapfile = open("/etc/opt/agocontrol/events.pck","w")
		pickle.dump(eventmap, eventmapfile)
		eventmapfile.close()
	except IOError, e:
		pass

def reportdevice(uuid, type='event', product=''):
	try:
		content = {}
		content["devicetype"]=type
		content["uuid"] = uuid
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

def removedevice(uuid):
	try:
		content = {}
		content["uuid"] = uuid
		message = Message(content=content,subject="event.device.remove")
		sender.send(message)
	except SendError, e:
		print e

syslog.syslog(syslog.LOG_NOTICE, "agoevent.py startup")


# 1732f705-523a-4d58-a6de-8dfd2a29d811 - vorzimmer
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"] = {}
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["event"]  = "event.environment.temperaturechanged"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"] = {}
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][0] = {}
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][0]["lval"]  = "level"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][0]["comp"]  = "lt"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][0]["rval"]  = "23.9"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][1] = {}
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][1]["lval"]  = "uuid"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][1]["comp"]  = "eq"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["criteria"][1]["rval"]  = "4830bd51-d553-4e2c-b0ec-2701c050a334"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["nesting"] = "criteria[0] and criteria[1]"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["action"]  = {}
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["action"]["command"]   = "on"
# eventmap["808a41b2-f8b5-4bee-97c4-b911ede02ace"]["action"]["uuid"]   = "1e68018f-e43b-4279-a314-0a2c0c615d5c"

for uuid in eventmap.iterkeys():
	reportdevice(uuid)

bp = BoolParser()

while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.content:
			if 'command' in message.content:
				if message.content['command'] == 'discover':
					syslog.syslog(syslog.LOG_NOTICE, "device discovery")
					for uuid in eventmap.iterkeys():
						reportdevice(uuid)
				if message.content['command'] == 'setevent':
					if 'eventmap' in message.content:
						myuuid = ""
						if 'uuid' in message.content:
							myuuid = message.content['uuid']
						else:
							myuuid = str(uuid4())
						print "setevent, eventmap: ", message
						syslog.syslog(syslog.LOG_NOTICE, "setevent %s - %s" % (myuuid, str(message.content['eventmap'])))
						eventmap[myuuid] = message.content['eventmap']
						savemap()
						reportdevice(myuuid)
						if message.reply_to:
							print "sending reply"
							replysender = session.sender(message.reply_to)
							response = Message(myuuid)
							print "response: ", response
							try:
								replysender.send(response)
							except SendError, e:
								print "Can't send ACK: ", e
							except NotFound, e:
								print "Can't send ACK: ", e
				if 'uuid' in message.content:
					uuid = message.content['uuid']
					if message.content['command'] == 'getevent':
						if message.content['uuid'] in eventmap:
							content = {}
							content["eventmap"] = eventmap[message.content['uuid']]
							content["uuid"] = message.content['uuid']
							replysender = session.sender(message.reply_to)
							response = Message(content=content)
							try:
								replysender.send(response)
							except SendError, e:
								print "Can't send reply: ", e
							except NotFound, e:
								print "Can't send reply: ", e
					if message.content['command'] == 'delevent':
						if message.content['uuid'] in eventmap:
							del eventmap[message.content['uuid']]
							savemap()
							removedevice(message.content['uuid'])
							if message.reply_to:
								replysender = session.sender(message.reply_to)
								response = Message("ACK")
								try:
									replysender.send(response)
								except SendError, e:
									print "Can't send ACK: ", e
								except NotFound, e:
									print "Can't send ACK: ", e
		if message.subject:
			if 'event.' in message.subject:
				for uuid in eventmap.iterkeys():
					if eventmap[uuid]["event"] == message.subject:
						print "found scenario", uuid, message.subject
						# print message
						criteria = {}
						for idx in eventmap[uuid]["criteria"]:
							criteria[str(idx)] = 0
							if eventmap[uuid]["criteria"][idx]["lval"] in message.content:
								lval = message.content[eventmap[uuid]["criteria"][idx]["lval"]]
								rval = eventmap[uuid]["criteria"][idx]["rval"]
								comp = eventmap[uuid]["criteria"][idx]["comp"]
								print "comparing", lval, comp, rval
								if 'lt' in comp:
									if float(lval) < float(rval):
										print float(lval), " < ", float(rval)
										criteria[str(idx)] = 1
								if 'gt' in comp:
									if float(lval) > float(rval):
										print float(lval), " > ",  float(rval)
										criteria[str(idx)] = 1
								if 'eq' in comp:
									try:
										if float(lval) == float(rval):
											print rval, " = ", lval
											criteria[str(idx)] = 1
									except ValueError, e:
										if lval == rval:
											print rval, " = ", lval
											criteria[str(idx)] = 1
						try:
							print "criteria results: ", criteria, bp.parse(eventmap[uuid]["nesting"], criteria)
							if bp.parse(eventmap[uuid]["nesting"], criteria):
								print "criteria is true. firing command"
								content = eventmap[uuid]["action"]
								action = Message(content=content)
								try:
									sender.send(action)
								except SendError, e:
									print e
						except KeyError, e:
							print "FATAL ERROR, KeyError in eval: ", eventmap[uuid], e
	except TypeError, e:
		print "TypeError in message handling: ", e
	except Empty, e:
		pass
	except ReceiverError, e:
		print e
		time.sleep(1)
