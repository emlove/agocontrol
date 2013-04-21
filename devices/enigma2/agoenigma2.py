#! /usr/bin/env python

import sys
import syslog
import time
import pickle
import optparse
import ConfigParser
import socket

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from xml.dom import minidom

import myavahi

import urllib
import urllib2

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
# sys.stderr = LogErr()

# read persistent uuid mapping from file
try:
	uuidmapfile = open("/etc/opt/agocontrol/enigma2-uuidmap.pck","r")
	uuidmap = pickle.load(uuidmapfile)
	uuidmapfile.close()
except IOError, e:
	uuidmap = {}

devices = {}

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

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
			uuidmapfile = open("/etc/opt/agocontrol/enigma2-uuidmap.pck","w")
			pickle.dump(uuidmap, uuidmapfile)
			uuidmapfile.close()
		except IOError, e:
			pass
	return uuidmap[path]

def reportdevice(path, type='settopbox', product='Dreambox/Enigma2'):
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

def discovery():
	for path in devices.iterkeys():
		reportdevice(path);

syslog.syslog(syslog.LOG_NOTICE, "agoenigma2.py startup")

syslog.syslog(syslog.LOG_NOTICE, "discovering devices")


def mycallback(name, host, port):
	if "dm500hd" in name or "dm600pvr" in name:
		# print "callback %s %s %s\n" % (name, host, port)
		devices[name] = host
		try:
			f = urllib2.urlopen('http://%s/web/about' % str(host))
			dom1 = minidom.parseString(f.read())
			e2model = dom1.getElementsByTagName('e2model')[0];
			print "Found %s on %s\n" % (e2model.childNodes[0].data,str(host))
			reportdevice(str(name))
		except:
			print "can't get enigma model\n" 

s = myavahi.zmqconf(mycallback)
s.browse_services("_workstation._tcp")

def getText(nodelist):
	rc = []
	for node in nodelist:
		if node.nodeType == node.TEXT_NODE:
			rc.append(node.data)
	return ' '.join(rc)

# enigma2 webif2 helpers
def zap(host, service):
	f=urllib2.urlopen('http://%s/web/zap?%s' % (host,urllib.urlencode({'sRef':service})))
	zapxml = minidom.parseString(f.read())
	status = zapxml.getElementsByTagName('e2state')[0].childNodes[0].data
	message = zapxml.getElementsByTagName('e2statetext')[0].childNodes[0].data
	print "Status: %s, text: %s\n" % (status,message)

def setvolume(host, volume):
	f=urllib2.urlopen('http://%s/web/vol?set=%s' % (host,volume))
	zapxml = minidom.parseString(f.read())
	status = zapxml.getElementsByTagName('e2result')[0].childNodes[0].data
	message = zapxml.getElementsByTagName('e2resulttext')[0].childNodes[0].data
	print "Status: %s, text: %s\n" % (status,message)

def setmute(host, mute):
	f=urllib2.urlopen('http://%s/web/vol?set=state' % host)
	zapxml = minidom.parseString(f.read())
	status = zapxml.getElementsByTagName('e2ismuted')[0].childNodes[0].data
	if bool(status) != bool(mute):
		f=urllib2.urlopen('http://%s/web/vol?set=mute' % host)
		zapxml = minidom.parseString(f.read())
		status = zapxml.getElementsByTagName('e2ismuted')[0].childNodes[0].data
	return bool(status)

def setpower(host, state):
	f=urllib2.urlopen('http://%s/web/powerstate?newstate=%s' % (host,state))
	zapxml = minidom.parseString(f.read())
	status = zapxml.getElementsByTagName('e2instandby')[0].childNodes[0].data
	print "Status: %s\n" % status

def getepgservicenext(host, service):
	f=urllib2.urlopen('http://%s/web/epgservicenext?sRef=%s' % (host,service))
        epgxml = minidom.parseString(f.read())
	title = epgxml.getElementsByTagName('e2eventtitle')[0].childNodes[0].data
	description = getText(epgxml.getElementsByTagName('e2eventdescriptionextended')[0].childNodes)
	return (title, description)

def getepgservicenow(host, service):
	f=urllib2.urlopen('http://%s/web/epgservicenow?sRef=%s' % (host,service))
	epgxml = minidom.parseString(f.read())
	title = epgxml.getElementsByTagName('e2eventtitle')[0].childNodes[0].data
	description = getText(epgxml.getElementsByTagName('e2eventdescriptionextended')[0].childNodes)
	return (title, description)

def getepgnownext(host, bouquet):
	epg = {}
	f=urllib2.urlopen('http://%s/web/epgnownext?%s' % (host, urllib.urlencode({'bRef':bouquet})))
        epgxml = minidom.parseString(f.read())
	for event in epgxml.getElementsByTagName('e2event'):
		e2event = {}
		e2event['title'] = event.getElementsByTagName('e2eventtitle')[0].childNodes[0].data
		e2event['id'] = event.getElementsByTagName('e2eventid')[0].childNodes[0].data
		e2event['start'] = event.getElementsByTagName('e2eventstart')[0].childNodes[0].data
		e2event['duration'] = event.getElementsByTagName('e2eventstart')[0].childNodes[0].data
		e2event['description'] = getText(epgxml.getElementsByTagName('e2eventdescriptionextended')[0].childNodes)
		servicename = getText(epgxml.getElementsByTagName('e2eventservicename')[0].childNodes)
		if servicename not in epg:
			epg[servicename] = []
		epg[servicename].append(e2event)
	return epg

def getallservices(host):
	services={}

	f=urllib2.urlopen('http://%s/web/getallservices' % host)
	servicesxml = minidom.parseString(f.read())
	e2bouquets = servicesxml.getElementsByTagName('e2bouquet');
	for bouquet in e2bouquets:
		bouquetname = bouquet.getElementsByTagName('e2servicename')[0].childNodes[0].data
		print "Found Servicename: %s\n" % bouquetname
		services[bouquetname] = {}
		for service in bouquet.getElementsByTagName('e2service'):
			servicename = service.getElementsByTagName('e2servicename')[0].childNodes[0].data
			serviceref =  service.getElementsByTagName('e2servicereference')[0].childNodes[0].data
			services[bouquetname][servicename]=serviceref
	return services

def getbouquets(host):
	bouquets = {}

        f=urllib2.urlopen('http://%s/web/getallservices' % host)
        servicesxml = minidom.parseString(f.read())
        e2bouquets = servicesxml.getElementsByTagName('e2bouquet');
        for bouquet in e2bouquets:
                bouquetname = bouquet.getElementsByTagName('e2servicename')[0].childNodes[0].data
                bouquetref = bouquet.getElementsByTagName('e2servicereference')[0].childNodes[0].data
		bouquets[bouquetname]=bouquetref
	return bouquets

#services = getallservices('192.168.80.9')
#bouquets = getbouquets('192.168.80.9')

#print services
#print bouquets
#(title, description) = getepgservicenext('192.168.80.9',services["Favourites (TV)"]['Das Erste HD'])
#print "%s = %s" % (title, description)
#print getepgnownext('192.168.80.9',bouquets['Favourites (TV)'])

while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.content:
			if 'command' in message.content:
				print message
				if message.content['command'] == 'discover':
					syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
					discovery()
				if message.content['command'] == 'inventory':
					syslog.syslog(syslog.LOG_NOTICE, "ignoring inventory command")
				else:
					for (name, uuid) in uuidmap.iteritems():
						if message.content['uuid'] == uuid:
							print name, uuid
							host = devices[name]
							result = 'ACK'
							if message.content['command'] == 'on':
								setpower(host, 4)
							if message.content['command'] == 'off':
								setpower(host, 5)
							if message.content['command'] == 'mute':
								setmute(host, True)
							if message.content['command'] == 'unmute':
								setmute(host, False)
							if message.content['command'] == 'mutetoggle':
								setvolume(host, "mute")
							if message.content['command'] == 'vol+':
								setvolume(host, "up")
							if message.content['command'] == 'vol-':
								setvolume(host, "down")
							if message.content['command'] == 'setlevel':
								setvolume(host, 'set%s' % message.content['level'])
							if message.content['command'] == 'zap':
								channel = message.content['channel']
								services = getallservices(host)
								for (bouquet, servicelist) in services.iteritems():
									if channel in servicelist:
										zap(host, servicelist[channel])
							if message.content['command'] == 'getepg':
								epg={}
								for (bouquet, bref) in getbouquets(host).iteritems():
									epg[bouquet] = getepgnownext(host,bref)
								result = epg
								print result
							# send reply
							if message.reply_to:
								replysender = session.sender(message.reply_to)
								response = Message(result)
								try:
									replysender.send(response)
								except SendError, e:
									print "Can't send ACK: ", e
	except Empty, e:
		pass
	except KeyError, e:
		print "key error in command evaluation", e
	except ReceiverError, e:
		print e
		time.sleep(1)




