#!/usr/bin/env python
#
# resolver - service and name resolver for the AMQP based automation control
#
# Copyright (c) 2012 Harald Klein <hari@vt100.at>
#

try:
	from pysqlite2 import dbapi2 as sqlite3
except ImportError:
	import sqlite3

dbconn = sqlite3.connect('/etc/opt/agocontrol/inventory.db')

def getdevicename (uuid):
	print uuid
	c = dbconn.cursor()
	t = (uuid,)
	result = ""
	try:
		c.execute('select name from devices where uuid=?',t)
		for row in c:
			result = row[0]
		c.close()
		return result
	except sqlite3.InterfaceError, e:
		return ""

def getdeviceroom (uuid):
	c = dbconn.cursor()
	t = (uuid,)
	result = ""
	try:
		c.execute('select room from devices where uuid=?',t)
		for row in c:
			result = row[0]
		c.close()
		return result
	except sqlite3.InterfaceError, e:
		return ""

def setdevicename (uuid, name):
	c = dbconn.cursor()
	t = (name,uuid)
	if getdevicename(uuid) == "":
		c.execute('insert into devices (name, uuid) VALUES(?,?)',t)
	else:
		c.execute('update devices set name=? where uuid=?',t)
	dbconn.commit()
	c.close()

def getroomname (uuid):
	c = dbconn.cursor()
	t = (uuid,)
	result = ""
	c.execute('select name from rooms where uuid=?',t)
	for row in c:
		result = row[0]
	c.close()
	return result

def setroomname (uuid, name):
	c = dbconn.cursor()
	t = (name, uuid)
	if getroomname(uuid) == "":
		c.execute('insert into rooms (name, uuid) VALUES(?,?)',t)
	else:
		c.execute('update rooms set name=? where uuid=?',t)
	dbconn.commit()
	c.close()

def setdeviceroom (deviceuuid, roomuuid):
	c = dbconn.cursor()
	t = (roomuuid, deviceuuid)
	c.execute('update devices set room=? where uuid=?',t)
	dbconn.commit()
	c.close()
	
def getdeviceroomname (uuid):
	c = dbconn.cursor()
	t = (uuid,)
	result = ""
	c.execute('select room from devices where uuid=?',t)
	for row in c:
		result = getroomname(row[0])
	c.close()
	return result
	
def getrooms():
	c = dbconn.cursor()
	c.execute ('select uuid, name, location from rooms')
	rooms = {}
	for row in c:
		rooms[row[0]] = {"name": row[1], "location": row[2]}
	c.close()
	return rooms	

def deleteroom (uuid):
	c = dbconn.cursor()
	t = (uuid,)
	c.execute('delete from rooms where uuid=?',t)
	c.execute('update devices set room="" where uuid=?',t)
	c.close()
