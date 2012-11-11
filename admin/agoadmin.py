#!/usr/bin/python

import pprint
import optparse
from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

from ConfigParser import * 

import os
import cherrypy
from cherrypy.lib import file_generator

import StringIO

from mako.exceptions import RichTraceback
from mako.template import Template
from mako.lookup import TemplateLookup

from connector import *
import simplejson
import webbrowser
import re

import urllib2
import subprocess
import datetime

lookup = TemplateLookup(directories=['tpl'], module_directory='mod')

PATH = os.path.abspath(os.path.dirname(__file__))

config = RawConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
	SYSTEM_USERNAME = config.get("system","username")
except ConfigParser.NoOptionError, e:
	SYSTEM_USERNAME = "agocontrol"

try:
	SYSTEM_PASSWORD = config.get("system","password")
except ConfigParser.NoOptionError, e:
	SYSTEM_PASSWORD = "letmein"

try:
	SYSTEM_BROKER = config.get("system","broker")
except ConfigParser.NoOptionError, e:
	SYSTEM_BROKER = "localhost"

try:
	SYSTEM_DEBUG = config.get("system","debug")
except ConfigParser.NoOptionError, e:
	SYSTEM_DEBUG = "WARN"

try:
	SYSTEM_UUID = config.get('system', 'uuid')
except ConfigParser.NoOptionError, e:
	SYSTEM_UUID = ""

try:
	DEVICES_QUEUE = config.get('devices', 'queue')
except ConfigParser.NoOptionError, e:
	DEVICES_QUEUE = "agocontrol"

try:
	PORT = config.get('admin', 'port')
except:
	PORT = 8000

conn = Connector(SYSTEM_BROKER, SYSTEM_USERNAME, SYSTEM_PASSWORD, DEVICES_QUEUE)

def discover():
	message = conn.get_inventory()

	if message.content:
		return message.content
	else:
		return {}

def getDevices(content):
	devices = []
	if "inventory" in content:
		for id, device in content["inventory"].iteritems():
			newdevice = device
			newdevice["id"] = id
			if "room" in device:
				if device["room"] in content["rooms"]:
					newdevice["roomname"] =  content["rooms"][device["room"]]["name"]
				else:
					newdevice["roomname"] = ""
			devices.append(newdevice)
	return devices

def getRooms(content):
	rooms = []
	if "rooms" in content:
		for id, room in content["rooms"].iteritems():
			newroom = room
			newroom["id"] = id
			rooms.append(newroom)
	return rooms

config={
	'global': {
		'server.socket_host': '0.0.0.0',
		'server.socket_port': PORT,
		'server.thread_pool': 10,
		'tools.sessions.on': True,
		'tools.staticdir.root': PATH,
	},
	'/': {
		'tools.staticdir.on': True,
		'tools.staticdir.dir': 'static',
	}
}

class Command:
	def default(self, uuid, command):
		conn.send_command(uuid, command, "")
	default.exposed = True

class CreateRoom:
	def default(self, name):
		conn.create_room(name)
	default.exposed = True

class DeleteRoom:
	def default(self, uuid):
		conn.delete_room(uuid)
	default.exposed = True

class DeleteScenario:
	def default(self, uuid):
        	#cherrypy.response.headers['Content-Type'] = 'application/json'
		conn.delete_scenario(uuid)
		#return uuid
	default.exposed = True

class SetRoomName:
    @cherrypy.expose
    def submit(self, roomname, id, uuid):
        cherrypy.response.headers['Content-Type'] = 'application/json'
	conn.set_room_name(uuid, roomname)
	return roomname

class SetDeviceName:
    @cherrypy.expose
    def submit(self, devicename, id, uuid):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        #return simplejson.dumps(dict(title="Hello, %s" % devicename))
        #return simplejson.dumps(devicename)
	conn.set_device_name(uuid, devicename)
	return devicename

class SetDeviceRoom:
    @cherrypy.expose
    def submit(self, deviceroom, id, uuid):
        cherrypy.response.headers['Content-Type'] = 'application/json'
	conn.set_device_room(uuid, deviceroom)
	return deviceroom


class Rooms:
	def default(self):
		try:
			tmpl = lookup.get_template("rooms.html")
			inventory = discover()
			return tmpl.render(rooms=getRooms(inventory))
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)
	default.exposed = True

class Setup:
	def default(self):
		try:
			tmpl = lookup.get_template("setup.html")
			inventory = discover()
			return tmpl.render(inventory=getDevices(inventory), rooms=getRooms(inventory), schema=inventory["schema"])
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)
	default.exposed = True

class Scenario:
	def default(self):
		try:
			tmpl = lookup.get_template("scenario.html")
			inventory = discover()
			return tmpl.render(inventory=getDevices(inventory), rooms=getRooms(inventory), schema=inventory["schema"])
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)
	default.exposed = True


class Root:
	@cherrypy.expose
	def index(self):
		try:
			tmpl = lookup.get_template("index.html")
			inventory = discover()
			return tmpl.render(salutation="Hello", inventory=getDevices(inventory), rooms=getRooms(inventory))
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)

	@cherrypy.expose
	def cloudcert(self):
		try:
			tmpl = lookup.get_template("cloudcert.html")
			return tmpl.render()
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)

	@cherrypy.expose
	def activate(self, username, password, pin):
		try:
			tmpl = lookup.get_template("cloudactivate.html")
			url = "http://cloud.agocontrol.com/agoka/?uuid=%s&username=%s&password=%s" % (SYSTEM_UUID, username, password)
			file_name = "/tmp/%s.p12" % SYSTEM_UUID 
			u = urllib2.urlopen(url)
			buffer = u.read()
			if 'Incorrect username or password.' in buffer:
				result = "Activation failed, please verify that username and password are correct. Please also check that the installation uuid is active in the ago cloud service"
			else: 
				f = open(file_name, 'wb')
				f.write(buffer)
				f.close()
				command = "/opt/agocontrol/bin/agocloud-import.sh %s %s" % (file_name, pin)
				if os.system(command) == 0:
					result = "Activation certificate was installed successfully"
				else:
					result = "Error, could not import certificate, check pin"
			return tmpl.render(content=result)
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)

	@cherrypy.expose
	def getvideoframe(self, uuid):
		try:		
			message = conn.get_videoframe(uuid)
			buffer = StringIO.StringIO(message.content)
	
			cherrypy.response.headers['Content-Type'] = "image/jpg"
			return file_generator(buffer)
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)

	@cherrypy.expose
	def savevideoframe(self, uuid):
		try:		
			message = conn.get_videoframe(uuid)
			now = datetime.datetime.now()
	
			basedir = "archive/" + SYSTEM_UUID + "/" + str(now.year) + "/" + str(now.month) + "/" + str(now.day) + "/" 
			subprocess.call(['mkdir', '-p', basedir])
			filename = basedir + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second) + ".jpg"
			myFile = file(filename, 'wb')
			myFile.write(message.content)
			myFile.close()
			return (filename)
		except:
			traceback = RichTraceback()
			error_tmpl = lookup.get_template("error-tpl.html")
			return error_tmpl.render(traceback = traceback.traceback)

class GetRoomsJson(object):
    @cherrypy.expose
    def default(self, id):
	inventory = discover()
	rooms = {}
	for id, roominfo in inventory["rooms"].iteritems():
		rooms[id] = roominfo["name"]

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(rooms)

class GetInventory(object):
    @cherrypy.expose
    def default(self):
	inventory = discover()

        cherrypy.response.headers['Content-Type'] = 'application/json'
        return simplejson.dumps(inventory)

class GetSchema(object):
    @cherrypy.expose
    def default(self):
	tpl = lookup.get_template("schema.html")
	inventory = discover()
	pp = pprint.PrettyPrinter(indent=4)
        return tpl.render(content=pp.pformat(inventory["schema"]))

class Event(object):

    @cherrypy.expose
    def default(self):
        inventory = discover()
        tpl = lookup.get_template("events.html")
        return tpl.render(eventMap=simplejson.dumps(inventory["schema"]["events"]),
                          commands=simplejson.dumps(inventory["schema"]["commands"]),
                          deviceTypes=simplejson.dumps(inventory["schema"]["devicetypes"]),
                          devices=simplejson.dumps(getDevices(inventory)),
			  inventory=getDevices(inventory), rooms=getRooms(inventory), schema=inventory["schema"])

    idx = 0

    @cherrypy.expose
    def save(self, data, action, event_name):
        map = self.createEventMap(data)
        map["action"] = simplejson.loads(action)
        response = conn.create_event(map)
	if response:
		if response.content:
			uuid = response.content
			conn.set_device_name(uuid, simplejson.loads(event_name))
			return "OK"
	else:
		return "Error"

    def parseElement(self, map, elem):
        nesting = ""

        """ 'empty' events like 'sun did rise' """
        if not "sub" in elem:
            return "True"

        for obj in elem["sub"]:
            if "param" in obj:
                map["criteria"][str(self.idx)] = {}
                map["criteria"][str(self.idx)]["lval"] = obj["param"]
                map["criteria"][str(self.idx)]["comp"] = obj["comp"]
                map["criteria"][str(self.idx)]["rval"] = str(obj["value"])
                if nesting == "":
                    nesting = "(criteria[\"%d\"]" % self.idx
                else:
                    nesting += " %s criteria[\"%d\"]" % (elem["type"], self.idx)
                self.idx = self.idx + 1
            else:
                nesting += " %s (%s)" % (elem["type"],  self.parseElement(map, obj))

        return nesting + ")"

    def createEventMap(self, input):
        data = simplejson.loads(input)

        map = {}
        map["criteria"] = {}
        map["nesting"] = ""
        map["event"] = data["path"]
        
        self.idx = 0
        
        for elem in data["elements"]:
            map["nesting"] += self.parseElement(map, elem)
            self.idx = self.idx + 1
        
        """ add the toplevel operator """
        map["nesting"] = map["nesting"].replace(")(", ") " + data["conn"] + " (")

        """ remove useless and/or suffixes """
        map["nesting"] = map["nesting"].strip()
        regex = re.compile("^(and|or)");
        map["nesting"] = regex.sub("", map["nesting"])
        map["nesting"] = map["nesting"].strip()
        
        if not map["criteria"]:
            map["nesting"] = "True"

        return map

    @cherrypy.expose
    def edit(self, uuid):
        pp = pprint.PrettyPrinter(indent=4)
        inventory = discover()
        response = conn.get_event(uuid)
        if response:
            if response.content:
                data = response.content
                tpl = lookup.get_template("edit_event.html")
                devs = getDevices(inventory)
                eventName = ""
                for dev in devs:
                    if dev["id"] == uuid:
                        eventName = dev["name"]
                        break
                return tpl.render(eventMap=simplejson.dumps(inventory["schema"]["events"]),
                              commands=simplejson.dumps(inventory["schema"]["commands"]),
                              deviceTypes=simplejson.dumps(inventory["schema"]["devicetypes"]),
                              devices=simplejson.dumps(getDevices(inventory)),
                              currentEvent=self.mapToJSON(data["eventmap"]["event"], simplejson.dumps(data["eventmap"])),
                              event_name=eventName,
                              action=simplejson.dumps(data["eventmap"]["action"]),
                              uuid=uuid)
        else:
            return "Error, response is None"        

    @cherrypy.expose
    def do_edit(self, data, action, uuid, event_name):
        map = self.createEventMap(data)
        map["action"] = simplejson.loads(action)
        response = conn.edit_event(uuid, map)
        if response:
            if response.content:
                response.content
                conn.set_device_name(uuid, simplejson.loads(event_name))
                return "OK"
	else:
		return "Error"

    def mapToJSON(self, event, str):
        map = simplejson.loads(str)
        
        criteria = {}
        for idx in map["criteria"]:
            criteria[idx] = {}
            criteria[idx]["path"] = map["event"]
            criteria[idx]["comp"] = map["criteria"][idx]["comp"]
            criteria[idx]["param"] = map["criteria"][idx]["lval"]
            criteria[idx]["value"] = map["criteria"][idx]["rval"]

        res = {}
        res["conn"] = "and";
        if map["nesting"] == "True":
            res["elements"] = []
        else:
            res["elements"] = [self.parseGroup(map["nesting"], criteria)]
        res["path"] = event

        return simplejson.dumps(res)

    def getCriteriaIdx(self, str):
        p = re.compile(".+([0-9]).+")
        match = p.match(str)
        return match.groups()[0]

    def parseGroup(self, str, criteria):
        print str
        sub = []
        remove_p = re.compile("(^\()|(\)$)")
        str = remove_p.sub("", str)
        p = re.compile("(and|or)")
        type = "and"
        data = p.split(str)

        for i in range(len(data)):
            substr = data[i]
            if substr == "and" or substr == "or":
                type = substr
                continue
            if substr.strip().startswith("("):
                next = ""
                for j in range(i, len(data)):
                    next += data[j]
                sub.append(self.parseGroup(remove_p.sub("", next.strip()), criteria))
                break
            sub.append(criteria[self.getCriteriaIdx(substr)])

        return {"sub" : sub, "type" : type}

    @cherrypy.expose
    def delete(self, uuid):
    	conn.delete_event(uuid)


class SetDeviceLevel:
	def default(self, uuid, command, level):
		conn.send_command(uuid, command, level)
	default.exposed = True

class CreateScenario(object):
	@cherrypy.tools.json_in()
	def default(self):
		# cl = cherrypy.request.headers['Content-Length']
		# rawbody = cherrypy.request.body.read(int(cl))
		# body = simplejson.loads(rawbody)
		print "creating scenario" 
		print cherrypy.request.json
		scenariomap = {}
		idx = 0
		for command in cherrypy.request.json:
			scenariomap[str(idx)]=command
			idx = idx + 1
		print scenariomap
		message = conn.create_scenario(scenariomap)
		# return uuid
		return message.content
	default.exposed = True

class EditScenario:
    @cherrypy.expose
    def default(self, uuid):
        scenario = conn.get_scenario(uuid)
        map = scenario.content
        inventory = discover()  
        devs = getDevices(inventory)
        scenarioName = ""
        for dev in devs:
            if dev["id"] == uuid:
                scenarioName = dev["name"]
                break
        tpl = lookup.get_template("edit_scenario.html")
        return tpl.render(inventory=getDevices(inventory), rooms=getRooms(inventory), uuid=uuid,
                         schema=inventory["schema"], name=scenarioName, commands = simplejson.dumps(map["scenariomap"]))

    @cherrypy.expose
    def doEdit(self, uuid, commands, name):
        scenariomap = {}
        map = simplejson.loads(commands)
        idx = 0
        for command in map:
            if "command" in command:
    	        scenariomap[str(idx)] = command
	        idx = idx + 1

        print scenariomap

        response = conn.edit_scenario(uuid, scenariomap)

        if response:
            if response.content:
	            uuid = response.content
	            conn.set_device_name(uuid, name)
	            return "OK"
        else:
            return "Error"

root = Root()
root.command = Command()
root.rooms = Rooms()
root.setup = Setup()
root.scenario = Scenario()
root.createroom = CreateRoom()
root.deleteroom = DeleteRoom()
root.deletescenario = DeleteScenario()
root.editscenario = EditScenario()
root.setroomname = SetRoomName()
root.setdevicename = SetDeviceName()
root.setdeviceroom = SetDeviceRoom()
root.setdevicelevel = SetDeviceLevel()
root.get_rooms = GetRoomsJson()
root.getinventory = GetInventory()
root.schema = GetSchema()
root.event = Event()
root.createscenario = CreateScenario()

cherrypy.quickstart(root, '/', config)


