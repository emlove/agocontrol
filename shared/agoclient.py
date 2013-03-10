import syslog
import sys
import ConfigParser
import simplejson

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

def getConfigOption(section, option, default):
	try:
		value = config.get(section,option)
	except ConfigParser.NoOptionError, e:
		value = default
	return value

class AgoConnection:
	def __init__(self, instance):
		self.instance=instance
		syslog.syslog(syslog.LOG_NOTICE, "connecting to broker")
		broker = getConfigOption("system", "broker", "localhost")
		username = getConfigOption("system", "username", "agocontrol")
		password = getConfigOption("system", "password", "letmein")
		self.connection = Connection(broker, username=username, password=password, reconnect=True)
		self.connection.open()
		self.session = self.connection.session()
		self.receiver = self.session.receiver("agocontrol; {create: always, node: {type: topic}}")
		self.sender = self.session.sender("agocontrol; {create: always, node: {type: topic}}")
		self.devices = {}
		self.uuids = {}
		self.handler = None
		self.loadUuidMap()

	def addHandler(self, handler):
		self.handler = handler

	def internalIdToUuid(self, internalid):
		for uuid in self.uuids:
			if (self.uuids[uuid] == internalid):
				return uuid

	def uuidToInternalId(self, uuid):
		try:
			return self.uuids[uuid]
		except KeyError, e:
			return None

	def storeUuidMap(self):
		with open('/etc/opt/agocontrol/uuidmap/' + self.instance + '.json' , 'w') as outfile:
			simplejson.dump(self.uuids, outfile)

	def loadUuidMap(self):
                with open('/etc/opt/agocontrol/uuidmap/' + self.instance + '.json' , 'r') as infile:
			self.uuids = simplejson.load(infile)

	def addDevice(self, internalid, devicetype):
		if (self.internalIdToUuid(internalid) == None):
			self.uuids[str(uuid4())]=internalid
			self.storeUuidMap()
		device = {}
		device["devicetype"] = devicetype
		device["internalid"] = internalid
		self.devices[self.internalIdToUuid(internalid)] = device

	def sendMessage(self, content):
		return self.sendmessage(None, content)

	def sendMessage(self, subject, content):
		try:
			message = Message(content=content, subject=subject)
			self.sender.send(message)
			return True
		except SendError, e:
			syslog.syslog(syslog.LOG_ERR, "Can't send message: " + e)
			return False

	def emitEvent(self, internalId, eventType, level, unit):
		content  = {}
		content["uuid"]=self.internalIdToUuid(internalId)
		content["level"]=level
		content["unit"]=unit
		return self.sendMessage(eventType, content)

	def reportDevices(self):
		syslog.syslog(syslog.LOG_NOTICE, "reporting child devices")
		for device in self.devices:
			content = {}
			content["devicetype"]  = self.devices[device]["devicetype"]
			content["uuid"]  = device
			content["internalid"]  = self.devices[device]["internalid"]
			content["handled-by"]  = self.instance
			self.sendMessage("event.device.announce", content)			

	def run(self):
		self.reportDevices()
		syslog.syslog(syslog.LOG_NOTICE, "startup complete, waiting for messages")
		while (True):
			try:
				message = self.receiver.fetch()
				if message.content:
					if 'command' in message.content:
						if message.content['command'] == 'discover':
							self.reportDevices()
						else:
							if 'uuid' in message.content:
								myid = self.uuidToInternalId(message.content["uuid"])
								if myid != None:
									#this is for one of our children
									if self.handler:
										self.handler(myid, message.content)
									if message.reply_to:
										replysender = self.session.sender(message.reply_to)
										response = Message("ACK")
										try:
											replysender.send(response)
										except SendError, e:
											syslog.syslog(syslog.LOG_ERR, "can't send reply: " + e)
			except Empty, e:
				pass

			except ReceiverError, e:
				syslog.syslog(syslog.LOG_ERR, "can't receive message: " + e)
				time.sleep(1)
