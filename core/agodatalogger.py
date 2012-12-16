#!/usr/bin/env python
#
# datalogger - logs data to sqlite db and generates graph data for the AMQP based automation control
#
# Copyright (c) 2012 Christoph Jaeger office@diakonesis.at>
#
# create sqlite table:
# CREATE TABLE data(id INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT, environment TEXT, unit TEXT, level REAL, timestamp TIMESTAMP);


import sys
import syslog
import ConfigParser, os

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from pysqlite2 import dbapi2 as sqlite3
import sqlite3 as lite
import datetime

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

# get sqlite connection
con = lite.connect('agodatalogger.db')

connection = Connection(broker, username=username, password=password, reconnect=True)
try:
	connection.open()
	session = connection.session()
	receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
	receiver.capacity=100
	#sender = session.sender("agocontrol; {create: always, node: {type: topic}}")
	while True:
		try:
			message = receiver.fetch(timeout=1)
			if 'level' in message.content:
                		uuid = message.content["uuid"]
				environment =  message.subject.replace('environment.','').replace('changed','').replace('event.','')
				if 'unit' in message.content:
                			unit =  message.content["unit"]
				else:
					unit = ""
                		level =  message.content["level"]
				try:
                			with con:
                    				cur = con.cursor()
                    				cur.execute("INSERT INTO data VALUES(null,?,?,?,?,?)", (uuid,environment,unit,level,datetime.datetime.now()))
                    				newId = cur.lastrowid
                    				print "Info: New record ID %s with values uuid: %s, environment: %s, unit: %s, level: %s" % (newId,uuid,environment,unit,level)
				except sqlite3.Error as e:
					print  "Error " + e.args[0]

			if 'command' in message.content:
				if message.content['command'] == 'getloggergraph':
					print "Got getloggergraph command"						

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
