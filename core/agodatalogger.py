#!/usr/bin/env python
#
# datalogger - logs data to sqlite db and generates graph data for the AMQP based automation control
#
# Copyright (c) 2012 Christoph Jaeger office@diakonesis.at>
 

import sys
import syslog

import agoclient

import sqlite3 as sqlite
import datetime
from dateutil.parser import *

import pandas
import pandas.io.sql as psql
import simplejson

client = agoclient.AgoConnection("datalogger")

# get sqlite connection
con = sqlite.connect('/var/opt/agocontrol/datalogger.db')

def GetGraphData(deviceid, start, end, env):
	uuid = deviceid
	start_date = start
	end_date = end
	environment = env

	try:
		cur = con.execute("""SELECT timestamp AS Date,
					level AS Level
					FROM data
					WHERE timestamp BETWEEN ? AND ? 
					AND environment=?
					AND uuid=?
					ORDER BY timestamp""", (parse(start_date), parse(end_date), environment, uuid))

		values = []
		row = cur.fetchone()
		while row:
			tmp = {}
			tmp["time"] = int(parse(row[0]).strftime("%s"))
			tmp["level"] = row[1]
			values.append(tmp)
			row = cur.fetchone()
		cur.close()


		return values

	except sqlite.Error as e:
		print  "Error " + e.args[0]


def messageHandler(internalid, content):
	if "command" in content:
		if content['command'] == 'getloggergraph':
			deviceid = content['deviceid']
			start = content['start']
			end = content['end']
			env = content['env']
			result = GetGraphData(deviceid, start, end, env)
			return { "values" : result }
		if content['command'] == 'getdeviceenvironments':
			sources = {}
			try:
				with con:
					cur = con.cursor()
					result = cur.execute('select distinct uuid, environment from data').fetchall()
					sources = {}
					for row in result:
						sources[row[0]] = row[1]
				print sources
			except sqlite.Error as e:
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
		except sqlite.Error as e:
			print  "Error " + e.args[0]

client.addEventHandler(eventHandler)

client.addDevice("dataloggercontroller", "dataloggercontroller")

# route stderr to syslog
class LogErr:
	def write(self, data):
		syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
# sys.stderr = LogErr()

syslog.syslog(syslog.LOG_NOTICE, "agodatalogger.py startup")
client.run()
