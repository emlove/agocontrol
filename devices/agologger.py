#! /usr/bin/env python

import sys
import syslog
import time
import pickle
import optparse
import ConfigParser

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
                               description="event logger")
parser.add_option("-b", "--broker", default="localhost", help="hostname of broker (default %default)")
parser.add_option("-u", "--username", default=username, help="specify a username")
parser.add_option("-P", "--password", default=password, help="specify a password")
# parser.add_option("-s", dest="syslog", action="store_true", help="also log to syslog")

opts, args = parser.parse_args()

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
sys.stderr = LogErr()

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)

connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

syslog.syslog(syslog.LOG_NOTICE, "agologger.py startup")

while True:
	try:
		message = receiver.fetch(timeout=1)
		if message.subject:
			if 'event' in message.subject:
				syslog.syslog(syslog.LOG_NOTICE, str(message.subject))
				syslog.syslog(syslog.LOG_NOTICE, str(message))
				# print message.subject
	except Empty, e:
		pass
	except ReceiverError, e:
		print e
		time.sleep(1)

