#! /usr/bin/env python

import sys
import syslog
import time
import pickle
import optparse
import threading
import ConfigParser

from array import array

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
	username = config.get("system","username")
except:
	username = "agocontrol"

try:
	password = config.get("system","password")
except:
	password = "letmein"

try:
	broker = config.get("system","broker")
except:
	broker = "localhost"

try:
	debug = config.get("system","debug")
except:
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
sys.stderr = LogErr()
sys.stdout = LogErr()

# read persistent uuid mapping from file
try:
	scenariomapfile = open("/etc/opt/agocontrol/scenarios.pck","r")
	scenariomap = pickle.load(scenariomapfile)
	scenariomapfile.close()
except IOError, e:
	scenariomap = {}

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

class RunScenario(threading.Thread):
	scenario = {}
	def __init__(self, scenario):
		threading.Thread.__init__(self)
		self.scenario = scenario
	def run(self):
		# print "executing scenario thread, sending ", self.scenario
		lst = self.scenario.keys()
		lst.sort()
		for idx in lst:
			content = self.scenario[idx]
			if 'command' in content:
				if content["command"]=="scenariosleep" and 'delay' in content:
					# print "sleeping: ", content["delay"]
					time.sleep(int(content["delay"]))
				else:
					try:
						# syslog.syslog(syslog.LOG_NOTICE, str(content))
						commandmessage=Message(content=content)
						sender.send(commandmessage)
					except SendError, e:
						print e
def savemap():
	try:
		scenariomapfile = open("/etc/opt/agocontrol/scenarios.pck","w")
		pickle.dump(scenariomap, scenariomapfile)
		scenariomapfile.close()
	except IOError, e:
		pass

def reportdevice(uuid, type='scenario', product=''):
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

syslog.syslog(syslog.LOG_NOTICE, "agoscenario.py startup")


# 1732f705-523a-4d58-a6de-8dfd2a29d811 - vorzimmer
# scenariomap = {}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"] = {}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"][0] = {}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"][0] = {"command":"on", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"][1] = {}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"][1] = {"command":"scenariosleep", "delay":"10"}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"][2] = {}
# scenariomap["ddc74f71-6525-4e37-aa9c-253a920321ba"][2] = {"command":"on", "uuid":"c81a868e-e3da-418a-9f4e-fbfa30dfdcb9"}

# savemap()

for uuid in scenariomap.iterkeys():
	reportdevice(uuid)

while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.content:
			if 'command' in message.content:
				if message.content['command'] == 'discover':
					syslog.syslog(syslog.LOG_NOTICE, "device discovery")
					for uuid in scenariomap.iterkeys():
						reportdevice(uuid)
				if 'uuid' in message.content and message.content['command'] == 'on':
					uuid = message.content['uuid']
					if uuid in scenariomap.iterkeys():
						# print "found scenario"
						syslog.syslog(syslog.LOG_NOTICE, "firing scenario %s" % uuid)
						t = RunScenario(scenariomap[uuid])
						t.setDaemon(True)
						t.start()
						if message.reply_to:
							replysender = session.sender(message.reply_to)
							response = Message("ACK")
							try:
								replysender.send(response)
							except SendError, e:
								print "Can't send ACK: ", e
							except NotFound, e:
								print "Can't send reply: ", e
				if message.content['command'] == 'getscenario':
					if 'uuid' in message.content:
						myuuid = message.content["uuid"]
						if myuuid in scenariomap:
							if message.reply_to:
								content = {}
								content["scenariomap"] = scenariomap[myuuid] 
								content["uuid"] = myuuid
								replysender = session.sender(message.reply_to)
								response = Message(content=content)
								try:
									replysender.send(response)
								except SendError, e:
									print "Can't send reply: ", e
								except NotFound, e:
									print "Can't send reply: ", e

				if message.content['command'] == 'setscenario':
					if 'scenariomap' in message.content:
						myuuid = ""
						if 'uuid' in message.content:
							myuuid = message.content["uuid"]
						else:
							myuuid = str(uuid4())
						syslog.syslog(syslog.LOG_NOTICE, "setscenario %s - %s" % (myuuid, str(message.content['scenariomap'])))
						scenariomap[myuuid] = message.content['scenariomap']
						savemap()
						reportdevice(myuuid)
						if message.reply_to:
							replysender = session.sender(message.reply_to)
							response = Message(myuuid)
							try:
								replysender.send(response)
							except SendError, e:
								print "Can't send ACK: ", e
							except NotFound, e:
								print "Can't send ACK: ", e
				if message.content['command'] == 'delscenario':
					if 'uuid' in message.content:
						myuuid = message.content["uuid"]
						if myuuid in scenariomap:
							del scenariomap[myuuid]
							savemap()
							removedevice(myuuid)
							if message.reply_to:
								replysender = session.sender(message.reply_to)
								response = Message("ACK")
								try:
									replysender.send(response)
								except SendError, e:
									print "Can't send ACK: ", e
								except NotFound, e:
									print "Can't send ACK: ", e
	except TypeError, e:
		print "TypeError in message handling: ", e
	except Empty, e:
		pass
	except ReceiverError, e:
		print e
		time.sleep(1)

