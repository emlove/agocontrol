import syslog
import sys
import ConfigParser
import simplejson

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)


def getConfigOption(section, option, default):
	config = ConfigParser.ConfigParser()
	try:
		config.read('/etc/opt/agocontrol/conf.d/' + section + '.conf')
		value = config.get(section,option)
	except:
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
		self.eventhandler = None
		self.loadUuidMap()

	def addHandler(self, handler):
		self.handler = handler
		
	def addEventHandler(self, eventhandler):
		self.eventhandler = eventhandler

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
		try:
			with open('/etc/opt/agocontrol/uuidmap/' + self.instance + '.json' , 'r') as infile:
				self.uuids = simplejson.load(infile)
		except:
			pass

	def emitDeviceAnnounce(self, uuid, device):
		content = {}
		content["devicetype"]  = device["devicetype"]
		content["uuid"]  = uuid
		content["internalid"]  = device["internalid"]
		content["handled-by"]  = self.instance
		self.sendMessage("event.device.announce", content)			

	def emitDeviceRemove(self, uuid):
		content = {}
		content["uuid"]  = uuid
		self.sendMessage("event.device.remove", content)			

	def addDevice(self, internalid, devicetype):
		if (self.internalIdToUuid(internalid) == None):
			self.uuids[str(uuid4())]=internalid
			self.storeUuidMap()
		device = {}
		device["devicetype"] = devicetype
		device["internalid"] = internalid
		self.devices[self.internalIdToUuid(internalid)] = device
		self.emitDeviceAnnounce(self.internalIdToUuid(internalid), device)

	def removeDevice(self, internalid):
		if (self.internalIdToUuid(internalid) != None):	
			self.emitDeviceRemove(self.internalIdToUuid(internalid))
			del self.devices[self.internalIdToUuid(internalid)]

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
			self.emitDeviceAnnounce(device, self.devices[device])

	def run(self):
		# self.reportDevices() # - this is now handled by the addDevice
		syslog.syslog(syslog.LOG_NOTICE, "startup complete, waiting for messages")
		while (True):
			try:
				message = self.receiver.fetch()
				session.acknowledge()
				if message.content:
					if 'command' in message.content:
						if message.content['command'] == 'discover':
							self.reportDevices()
						else:
							if 'uuid' in message.content:
								if message.content['uuid'] in self.devices:
									#this is for one of our children
									myid = self.uuidToInternalId(message.content["uuid"])
									if myid != None and self.handler:
										replydata = {}
										replydata["result"] = self.handler(myid, message.content)
										if message.reply_to:
											replysession = self.connection.session()
											try:
												replysender = replysession.sender(message.reply_to)
												try:
													response = Message(replydata)
												except:
													syslog.syslog(syslog.LOG_ERR, "can't encode reply")
													print "Can't encode reply\n"
													response = Message({})
												try:
													response.subject = self.instance
													replysender.send(response)
												except SendError, e:
													syslog.syslog(syslog.LOG_ERR, "can't send reply: " + e)
													print "Can't send reply\n"
												except AttributeError, e:
													syslog.syslog(syslog.LOG_ERR, "can't send reply: " + e)
													print "Can't send reply\n"
											except:
												syslog.syslog(syslog.LOG_ERR, "can't send reply")
												print "Can't send reply\n"
											replysession.close()
				if message.subject:
					if 'event' in message.subject and self.eventhandler:
						self.eventhandler(message.subject, message.content)
			except Empty, e:
				pass

			except ReceiverError, e:
				syslog.syslog(syslog.LOG_ERR, "can't receive message: " + e)
				time.sleep(0.05)
