#!/usr/bin/python
#
#   ago control Asterisk PBX interface
#
#   Copyright (c) 2012 Harald Klein <hari@vt100.at>
#
from starpy import manager
from twisted.internet import defer, reactor
import logging,os
import time
import signal
import pickle
import optparse
import ConfigParser

import agoclient

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

config = ConfigParser.ConfigParser()
config.read(agoclient.CONFDIR + '/config.ini')

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
	amihost = config.get("asterisk","host")
except:
	amihost = "localhost"
try:
	amiport = int(config.get("asterisk","port"))
except:
	amiport = 5038
try:
	amiusername = config.get("asterisk","username")
except:
	amiusername = "agocontrol"
try:
	amipassword = config.get("asterisk","password")
except:
	amipassword = "letmein"

parser = optparse.OptionParser(usage="usage: %prog <command> [options] [ PARAMETERS ... ]",
                               description="send automation control commands")
parser.add_option("-b", "--broker", default=broker, help="hostname of broker (default %default)")
parser.add_option("-u", "--username", default=username, help="specify a username")
parser.add_option("-P", "--password", default=password, help="specify a password")

opts, args = parser.parse_args()

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

log = logging.getLogger( 'agoasterisk' )
log.setLevel( logging.INFO )

running = True

# read persistent uuid mapping from file
try:
	uuidmapfile = open(agoclient.CONFDIR + "/asterisk-uuidmap.pck","r")
	uuidmap = pickle.load(uuidmapfile)
	uuidmapfile.close()
except IOError, e:
	uuidmap = {}

devices = {}


def lookupuuid(path):
	if path in uuidmap:
		pass
	else:
		newuuid = str(uuid4())
		uuidmap[path] = newuuid
		try:
			print "new uuid %s %s" % (newuuid, path)
			# uuid is new, try to store it
			print uuidmap
			uuidmapfile = open(agoclient.CONFDIR + "/asterisk-uuidmap.pck","w")
			pickle.dump(uuidmap, uuidmapfile)
			uuidmapfile.close()
		except IOError, e:
			pass
	return uuidmap[path]

def reportdevice(path, type='phone', product='Asterisk channel'):
	try:
		content = {}
		content["devicetype"]=type
		content["event"] = "announce"
		content["uuid"] = lookupuuid(path)
		content["internal-id"] = path
		content["product"] = product
		message = Message(content=content,subject="event.device.announce")
		sender.send(message)
	except SendError, e:
		print e

def sendCallEvent(path, callerid, extension):
	try:
		content = {}
		content["uuid"] = lookupuuid(path)
		content["callerid"] = callerid
		content["extension"] = extension
		message = Message(content=content,subject='event.telecom.call')
		sender.send(message)
	except SendError, e:
		print e

def sendHangupEvent(path):
	try:
		content = {}
		content["uuid"] = lookupuuid(path)
		message = Message(content=content,subject='event.telecom.hangup')
		sender.send(message)
	except SendError, e:
		print e

def signalHandler(signum, stackframe):
	""" stop the CommandReceiver thread and the reactor """
	global running
	print "Got signal: %s" % signum
	running=False
	reactor.callFromThread(reactor.stop)
signal.signal(signal.SIGINT, signalHandler)

class ListPeers():
	def __init__(self, host, port, username, password):
		self.host = host
		self.port = port
		self.username = username
		self.password = password
	def onConnect(self, ami):
		def onResult(result):
			# print 'Result', result
			for entry in result:
				# {'ipport': '60868', 'status': 'Unmonitored', 'chanobjecttype': 'peer', 'objectname': 'hari', 'realtimedevice': 'no', 'dynamic': 'yes', 'textsupport': 'no', 'acl': 'no', 'actionid': 'pluto-140451068050032-2', 'videosupport': 'no', 'channeltype': 'SIP', 'ipaddress': '192.168.80.23', 'event': 'PeerEntry', 'forcerport': 'yes'}
				if 'chanobjecttype' in entry:
					print "Line: %s/%s" % (entry['channeltype'], entry['objectname'])
					reportdevice("%s/%s" % (entry['channeltype'], entry['objectname']))
		def onError( reason ):
		    print reason.getTraceback()
		    return reason
		def onFinished( result ):
			pass
		dfl = ami.sipPeers()
		dfl.addCallbacks( onResult, onError)
		dfl.addCallbacks( onFinished, onFinished )
		return dfl
	def main(self):
		theManager = manager.AMIFactory(self.username,self.password)
		df = theManager.login(self.host,self.port).addCallback(self.onConnect)


class DialOut():
	"""initiate call"""
	def __init__(self, channel, context='local', extension='s', priority=1):
		self.channel = channel
		self.context = context
		self.extension = extension
		self.priority = priority
	def onConnect(self, ami):
		def onResult(result):
			print 'Result', result
		def onError( reason ):
		    print reason.getTraceback()
		    return reason
		def onFinished( result ):
			pass
		try:
			dfl = ami.originate(self.channel,self.context,self.extension,self.priority)
			dfl.addCallbacks( onResult, onError)
			dfl.addCallbacks( onFinished, onFinished )
			return dfl
		except starpy.error.AMICommandFailure, e:
			return None
	def main(self):
		theManager = manager.AMIFactory(amiusername, amipassword)
		df = theManager.login(amihost,amiport).addCallback(self.onConnect)

class CommandReceiver():
	def __init__(self,receiver):
		self.receiver = receiver
	def main(self):
		listPeers = ListPeers(amihost, amiport, amiusername, amipassword)
		reactor.callFromThread(listPeers.main)
		while running:
			try:
				message = receiver.fetch(timeout=1)
				if message.content:
					if 'command' in message.content:
						if 'uuid' in message.content:
							for (name, uuid) in uuidmap.iteritems():
								if message.content['uuid'] == uuid:
									# this is for one of our devices, handle it
									if message.content['command'] == 'dial' and 'number' in message.content:
										dial = DialOut(channel=name, extension=message.content['number'])
										reactor.callFromThread(dial.main)
						if message.content['command'] == 'discover':
							listPeers = ListPeers(amihost, amiport, amiusername, amipassword)
							reactor.callFromThread(listPeers.main)
			except Empty, e:
				pass
			except KeyError, e:
				print "key error in command evaluation", e
			except ReceiverError, e:
				print e
				time.sleep(1)



class ChannelTracker():
	"""Track open channels on the Asterisk server"""
	channels = {}
	thresholdCount = 20
	def main( self ):
		"""Main operation for the channel-tracking demo"""
		theManager = manager.AMIFactory(amiusername, amipassword)
		df = theManager.login(amihost,amiport).addCallback(self.onAMIConnect)
	def onAMIConnect( self, ami ):
		ami.status().addCallback( self.onStatus, ami=ami )
		ami.registerEvent( 'Hangup', self.onChannelHangup )
		ami.registerEvent( 'Newchannel', self.onChannelNew )
	def onStatus( self, events, ami=None ):
		"""Integrate the current status into our set of channels"""
		log.debug( """Initial channel status retrieved""" )
		for event in events:
			self.onChannelNew( ami, event )
	def onChannelNew( self, ami, event ):
		if 'channel' in event and 'calleridnum' in event and 'exten' in event:
			sendCallEvent(event['channel'], event['calleridnum'], event['exten'])
		"""Handle creation of a new channel"""
		print """Start on channel %s""" % event 
		try:
			opening = not self.channels.has_key( event['uniqueid'] )
			self.channels[ event['uniqueid'] ] = event 
			if opening:
				self.onChannelChange( ami, event, opening = opening )
		except KeyError, e:
			pass
	def onChannelHangup( self, ami, event ):
		"""Handle hangup of an existing channel"""
		if 'channel' in event:
			sendHangupEvent(event['channel'])
		try:
			del self.channels[ event['uniqueid']]
		except KeyError, err:
			log.warn( """Hangup on unknown channel %s""", event )
		else:
			print  """Hangup on channel %s""" % event 
		self.onChannelChange( ami, event, opening = False )
	def onChannelChange( self, ami, event, opening=False ):
		"""Channel count has changed, do something useful like enforcing limits"""
		if opening and len(self.channels) > self.thresholdCount:
			log.warn( """Current channel count: %s""", len(self.channels ) )
		else:
			log.info( """Current channel count: %s""", len(self.channels ) )

if __name__ == "__main__":
	logging.basicConfig()
	tracker = ChannelTracker()
	qpidreceiver = CommandReceiver(receiver)
	reactor.callInThread( qpidreceiver.main )
	reactor.callWhenRunning( tracker.main )
	reactor.run()
