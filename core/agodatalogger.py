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

import pandas
import pandas.io.sql as psql
import simplejson

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
# sys.stderr = LogErr()

# get sqlite connection
con = lite.connect('agodatalogger.db')


def GetGraphData(uuid, start, end, env, freq):
	uuid = uuid
	start_date = start
	end_date = end
	environment = env
	frequency = freq

	try:
		df = psql.read_frame("""SELECT timestamp AS Date,
		environment AS Env,
		unit AS Unit,
		level AS Level
		FROM data
		WHERE timestamp BETWEEN '""" + start_date + """' AND '""" + end_date + """' 
		AND environment='""" + environment + """'
		AND uuid='""" + uuid + """'
		ORDER BY timestamp""", con, index_col = 'Date')

		if not df.empty:
			df.index = [pandas.datetools.to_datetime(di) for di in df.index]

			ticks = df.ix[:, ['Level', 'Unit']]
			result = ticks

			unit = map(lambda x: x.strip(), str(result["Unit"]).splitlines(True))[0].split()[-1]

			ticks = ticks.asfreq('1Min', method='pad').prod(axis=1).resample(frequency, how='mean')

			date_range = pandas.DatetimeIndex(start=start_date, end=end_date, freq=frequency)

      			df2 = ticks.reindex(date_range).fillna(method='backfill').fillna(method='pad')

			data = map(lambda x: x.strip(), str(df2).splitlines(True))
			json_map = {}
			json_map["unit"] = unit
			json_map["values"] = {}
			for i in range(len(data) - 1):
				json_map["values"][data[i][:19]] = data[i][23:].split()

			return simplejson.dumps(json_map)
		else:
			return "No data"

	except sqlite3.Error as e:
		print  "Error " + e.args[0]

connection = Connection(broker, username=username, password=password, reconnect=True)
try:
	connection.open()
	session = connection.session()
	receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
	receiver.capacity=100
	sender = session.sender("agocontrol; {create: always, node: {type: topic}}")
	while True:
		try:
			message = receiver.fetch(timeout=1)
			if message.content: 
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
						uuid = message.content['uuid']
						start = message.content['start']
						end = message.content['end']
						env = message.content['env']
						freq = message.content['freq']
						result = GetGraphData(uuid, start, end, env, freq)
						print result

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
