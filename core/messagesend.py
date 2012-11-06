#!/usr/bin/env python
#
# messagesend - send AMQP messages containing automation control commands
#
# Copyright (c) 2012 Harald Klein <hari@vt100.at>
#

import optparse
from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

import ConfigParser

def nameval(string):
	index = string.find("=")
	if index >= 0:
		name = string[0:index]
		value = string[index+1:]
	else:
		name = string
		value = None
	return name, value

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
parser.add_option("-c", "--command", help="specify a command")
parser.add_option("-u", "--username", default=username, help="specify a username")
parser.add_option("-P", "--password", default=password, help="specify a password")
parser.add_option("-d", "--destination", help="uuid of the target device")
parser.add_option("-p", "--parameters", dest="parameters", action="append", default=[], metavar="KEY=VALUE", help="command parameter map")

opts, args = parser.parse_args()

content = {}

if opts.command:
	content["command"] = opts.command
if opts.parameters:
	for elem in opts.parameters:
		name, value = nameval(elem)
		content[name] = value
if opts.destination:
	content["uuid"] = opts.destination

connection = Connection(opts.broker, username=opts.username, password=opts.password, reconnect=True)
try:
	connection.open()
	session = connection.session()
	# we use the command topic exchange
	sender = session.sender("agocontrol; {create: always, node: {type: topic}}")
	message = Message(content=content)
	sender.send(message)
except SendError, e:
	print e
connection.close()
