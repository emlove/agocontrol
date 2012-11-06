#!/usr/bin/env python
#
# drain - output all messages of AMQP based automation control
#
# Copyright (c) 2012 Christoph Jaeger office@diakonesis.at>
#

import sys
import syslog
import ConfigParser, os

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

# route stderr to syslog
class LogErr:
	def write(self, data):
		syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
sys.stderr = LogErr()

connection = Connection(broker, username=username, password=password, reconnect=True)
try:
	connection.open()
	session = connection.session()
	receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
	receiver.capacity=100
	while True:
		try:
			message = receiver.fetch()
			print message

			session.acknowledge()
		except Empty:
			pass
except SendError, e:
	print e
except ReceiverError, e:
	print e
except KeyboardInterrupt:
	pass
finally:
	connection.close()
