#!/usr/bin/env python
#
# datalogger - logs data to sqlite db and generates graph data for the AMQP based automation control
#
# Copyright (c) 2012 Christoph Jaeger office@diakonesis.at>
 

import sys
import syslog

import agoclient

import sqlite3 as lite
import datetime

import pandas
import pandas.io.sql as psql
import simplejson

client = agoclient.AgoConnection("datalogger")

# get sqlite connection
con = lite.connect('/var/opt/agocontrol/datalogger.db')

def GetGraphData(deviceid, start, end, env, freq):
	uuid = deviceid
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
			data_map = {}
			data_map["unit"] = unit
			data_map["values"] = {}
			for i in range(len(data) - 1):
				data_map["values"][data[i][:19]] = data[i][23:].split()

			return data_map
		else:
			return "No data"

	except sqlite3.Error as e:
		print  "Error " + e.args[0]


def messageHandler(internalid, content):
	if "command" in content:
		if content['command'] == 'getloggergraph':
			deviceid = content['deviceid']
			start = content['start']
			end = content['end']
			env = content['env']
			freq = content['freq']
			result = GetGraphData(deviceid, start, end, env, freq)
			print result
			return result
		if message.content['command'] == 'getdeviceenvironments':
			sources = {}
			try:
				with con:
					cur = con.cursor()
					result = cur.execute('select distinct uuid, environment from data').fetchall()
					sources = {}
					for row in result:
						sources[row[0]] = row[1]
				print sources
			except lite.Error as e:
				print  "Error " + e.args[0]
			return sources

client.addHandler(messageHandler)

def eventHandler(subject, content):
	if 'level' in content and subject:
		uuid = content["uuid"]
		environment =  subject.replace('environment.','').replace('changed','').replace('event.','')
		if 'unit' in content:
			unit =  content["unit"]
		else:
			unit = ""
		level =  content["level"]
		try:
			with con:
				cur = con.cursor()
				cur.execute("INSERT INTO data VALUES(null,?,?,?,?,?)", (uuid,environment,unit,level,datetime.datetime.now()))
				newId = cur.lastrowid
				print "Info: New record ID %s with values uuid: %s, environment: %s, unit: %s, level: %s" % (newId,uuid,environment,unit,level)
		except sqlite3.Error as e:
			print  "Error " + e.args[0]

client.addEventHandler(eventHandler)

# route stderr to syslog
class LogErr:
	def write(self, data):
		syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

syslog.syslog(syslog.LOG_NOTICE, "agodatalogger.py startup")
client.run()
