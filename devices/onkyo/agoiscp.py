#! /usr/bin/env python

import sys
import syslog
import time
import socket

from core import eISCP
import commands

import agoclient

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

client = agoclient.AgoConnection("iscp")

devices = {}

def discovery(timeout=3):
	avrs = eISCP.discover(timeout)
	for avr in avrs:
		client.addDevice("%s:%s" % (avr.host, avr.port), "avreceiver")
		# reportdevice("%s:%s" % (avr.host, avr.port), product=avr.info['model_name']);

syslog.syslog(syslog.LOG_NOTICE, "agoiscp.py startup")

syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
discovery()

def messageHandler(internalid, content):
	if 'command' in content:
		avr = eISCP(str.split(internalid,':',2)[0], int(str.split(internalid,':',2)[1]))
		command = ''
		try:
			if content['command'] == 'on':
				command = 'system-power:on'
				avr.command(command)
			if content['command'] == 'off':
				command = 'system-power:standby'
				avr.command(command)
			if content['command'] == 'mute':
				command = 'audio-muting:on'
				avr.command(command)
			if content['command'] == 'unmute':
				command = 'audio-muting:off'
				avr.command(command)
			if content['command'] == 'mutetoggle':
				command = 'audio-muting:toggle'
				avr.command(command)
			if content['command'] == 'vol+':
				command = 'master-volume:level-up'
				avr.command(command)
			if content['command'] == 'vol-':
				command = 'master-volume:level-down'
				avr.command(command)
			if content['command'] == 'setlevel':
				if 'level' in content:
					level = int(content['level'])
					command = 'MVL%x' % level
					# print "sending raw", command
					avr.send_raw(command)
			if content['command'] == 'setinput':
				if 'input' in content:
					command = 'input-selector:%s' % content['input']
					avr.command(command)
		except ValueError, e:
			print e
	result = {}
	result["result"] = 0;
	return result

client.addHandler(messageHandler)

client.run()

