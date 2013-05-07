#
# Squeezebox client
#
# copyright (c) 2013 James Roberts <jimbob@jamesroberts.co.uk>
# Using agoclient sample code as guidance!

import agoclient
import squeezeboxserver
import threading
import time

client = agoclient.AgoConnection("squeezebox")

# if you need to fetch any settings from config.ini, use the getConfigOption call. The first parameter is the section name in the file (should be yor instance name)
# the second one is the parameter name, and the third one is the default value for the case when nothing is set in the config.ini

server = agoclient.getConfigOption("squeezebox", "server", "127.0.0.1:9000")
print "Server: " + server

squeezebox = squeezeboxserver.SqueezeboxServer(server)

# the messageHandler method will be called by the client library when a message comes in that is destined for one of the child devices you're handling
# the first parameter is your internal id (all the mapping from ago control uuids to the internal ids is handled transparently for you)
# the second parameter is a dict with the message content

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "on":
			print "switching on: " + internalid

			squeezebox.power(internalid, content["command"])

			client.emitEvent(internalid, "event.device.statechanged", "255", "")

		if content["command"] == "off":
			print "switching off: " + internalid

			squeezebox.power(internalid, content["command"])
			
			client.emitEvent(internalid, "event.device.statechanged", "0", "")
			
		if content["command"] == "play":
			print "Play: " + internalid

			squeezebox.playlist(internalid, content["command"])
			
			client.emitEvent(internalid, "event.mediaplayer.statechanged", content["command"], "")	
		
		if content["command"] == "pause":
			print "Pause: " + internalid

			squeezebox.playlist(internalid, content["command"])
			
			client.emitEvent(internalid, "event.mediaplayer.statechanged", content["command"], "")	
		
		if content["command"] == "stop":
			print "Stop: " + internalid

			squeezebox.playlist(internalid, content["command"])
			
			client.emitEvent(internalid, "event.mediaplayer.statechanged", content["command"], "")

# specify our message handler method
client.addHandler(messageHandler)

# of course you need to tell the client library about the devices you provide. The addDevice call expects a internal id and a device type (you can find all valid types
# in the schema.yaml configuration file). The internal id is whatever you're using in your code to distinct your devices. Or the pin number of some GPIO output. Or
# the IP of a networked device. Whatever fits your device specific stuff. The persistent translation to a ago control uuid will be done by the client library. The
# mapping is stored as a json file in /etc/opt/agocontrol/uuidmap/<instance name>.json
# you don't need to worry at all about this, when the messageHandler is called, you'll be passed the internalid for the device that you did specifiy when using addDevice()

# Discover the devices connected

players = squeezebox.players()

for p in players:
	print ("MAC: %s" % p['playerid'])
	client.addDevice(p['playerid'], "squeezebox")

#client.addDevice("MAC Address", "squeezebox")

# then we add a background thread. This is not required and just shows how to send events from a separate thread. This might be handy when you have to poll something
# in the background or need to handle some other communication. If you don't need one or if you want to keep things simple at the moment just skip this section.

# Use this to create a thread to listen for events from clients - but how??

#class testEvent(threading.Thread):
#    def __init__(self,):
#        threading.Thread.__init__(self)    
#    def run(self):
#    	level = 0
#        while (True):
#			client.emitEvent("125", "event.security.sensortriggered", level, "")
#			if (level == 0):
#				level = 255
#			else:
#				level = 0
#			time.sleep (5)
#      
#background = testEvent()
#background.setDaemon(True)
#background.start()

# now you should have added all devices, set up all your internal and device specific stuff, started everything like listener threads or whatever. The call to run()
# is blocking and will start the message handling
client.run()

