#! /usr/bin/env python

import sys
import syslog
import time
import socket

from xml.dom import minidom

import myavahi

import urllib
import urllib2

import agoclient

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

client = agoclient.AgoConnection("enigma2")

syslog.syslog(syslog.LOG_NOTICE, "agoenigma2.py startup")
syslog.syslog(syslog.LOG_NOTICE, "discovering devices")

def mycallback(name, host, port):
	if "dm500hd" in name or "dm600pvr" in name:
		# print "callback %s %s %s\n" % (name, host, port)
		try:
			f = urllib2.urlopen('http://%s/web/about' % str(host))
			dom1 = minidom.parseString(f.read())
			e2model = dom1.getElementsByTagName('e2model')[0];
			print "Found %s on %s\n" % (e2model.childNodes[0].data,str(host))
			client.addDevice(str(host), "settopbox")
		except:
			print "ERROR: Can't determine enigma version"

s = myavahi.zmqconf(mycallback)
s.browse_services("_workstation._tcp")

time.sleep(3)

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

def messageHandler(internalid, content):
	if "command" in content:
		host = internalid
		result = 'ACK'
		if content['command'] == 'on':
			setpower(host, 4)
		if content['command'] == 'off':
			setpower(host, 5)
		if content['command'] == 'mute':
			setmute(host, True)
		if content['command'] == 'unmute':
			setmute(host, False)
		if content['command'] == 'mutetoggle':
			setvolume(host, "mute")
		if content['command'] == 'vol+':
			setvolume(host, "up")
		if content['command'] == 'vol-':
			setvolume(host, "down")
		if content['command'] == 'setlevel':
			if 'level' in content:
				setvolume(host, 'set%s' % content['level'])
		if content['command'] == 'zap':
			if 'channel' in content:
				channel = content['channel']
				services = getallservices(host)
				for (bouquet, servicelist) in services.iteritems():
					if channel in servicelist:
						zap(host, servicelist[channel])
		if content['command'] == 'getepg':
			epg={}
			for (bouquet, bref) in getbouquets(host).iteritems():
				epg[bouquet] = getepgnownext(host,bref)
			result = epg
			print result

client.addHandler(messageHandler)

client.run()

