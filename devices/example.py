#
# ago client library example deivce
#
# copyright (c) 2013 Harald Klein <hari+ago@vt100.at>
#

# to use the client library we have to import it

import agoclient


# then we create an AgoConnection object. You need to specify an instance name as parameter. 
# This will be used to uniquely name the mappings file for internal id to uuid mapping and to identify the client devices ("handled-by" parameter)
# Examples for the instance name would be "zwave" for our z-wave device, "knx" for KNX, "owfs" for the one wire device, and so on.
# Just chose a name that is unique and speaks for itself. It is best practice to also use that instance name as section name in the config file
# if you need any config parameters.

client = agoclient.AgoConnection("example")


# the messageHandler method will be called by the client library when a message comes in that is destined for one of the child devices you're handling
# the first parameter is your internal id (all the mapping from ago control uuids to the internal ids is handled transparently for you)
# the second parameter is a dict with the message content

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "on":
			print "switching on: " + internalid

			# TODO: insert real stuff here, this is where you would do action and switch on your child device

			# depending on if the operation was successful, you want to report state back to ago control. We just send 255 in this case 
			# so that ago control changes the device state in the inventory to on

			client.emitEvent(internalid, "event.device.state", "255", "")

		if content["command"] == "off":
			print "switching off: " + internalid
			client.emitEvent(internalid, "event.device.state", "0", "")

# specify our message handler method
client.addHandler(messageHandler)

# if you need to fetch any settings from config.ini, use the getConfigOption call. The first parameter is the section name in the file (should be yor instance name)
# the second one is the parameter name, and the third one is the default value for the case when nothing is set in the config.ini

print agoclient.getConfigOption("test", "parameter", "0")


# of course you need to tell the client library about the devices you provide. The addDevice call expects a internal id and a device type (you can find all valid types
# in the schema.yaml configuration file). The internal id is whatever you're using in your code to distinct your devices. Or the pin number of some GPIO output. Or
# the IP of a networked device. Whatever fits your device specific stuff. The persistent translation to a ago control uuid will be done by the client library. The
# mapping is stored as a json file in /etc/opt/agocontrol/uuidmap/<instance name>.json
# you don't need to worry at all about this, when the messageHandler is called, you'll be passed the internalid for the device that you did specifiy when using addDevice()

# we add a switch and a dimmer 
client.addDevice("123", "dimmer")
client.addDevice("124", "switch")

# now you should have added all devices, set up all your internal and device specific stuff, started everything like listener threads or whatever. The call to run()
# is blocking and will start the message handling
client.run()

