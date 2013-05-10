#
# ago control for Mushroom Control
#
# Arduino Based Mushroom Control System 
#
# StateController states:
# 	0: idle
#	1: heat
#	2: cool
#	3: humidify
#	4: dehumidify
#	5: circulateair
#	6: freshair

# Variables:
#	AirHumidity.low 
#	AirHumidity.high
#	AirTemperature.low
#	AirTemperature.high
#	AirCircInterval
#
# copyright (c) 2013 Christoph Jaeger <office@diakonesis.at>
#

import agoclient
import threading
import time
import serial
import json

state = {"state":"","AirTemperature":"","AirHumidity":""}
variables = {"AirHumidity.low":"","AirHumidity.high":"","AirTemperature.low":"","AirTemperature.high":"","AirCircInterval":""}
sensors = {"AirTemperature":"","AirHumidity":""}


client = agoclient.AgoConnection("MushroomControl")

myport = agoclient.getConfigOption("MushroomControl", "device", "0")

s0 = serial.Serial(myport, 9600)


def inventory ():
	s0.write('{"content": {"command":"inventory"}}')

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "setvariable":
			try:
				myvalue = ""
				if "templow" in content:
					print "templow on " + internalid + " set to " + content["templow"]
					s0.write('{"content": { "variable":"AirTemperature.low", "value": "%s"}}' % int(content["templow"]))
				if "temphigh" in content:
					print "temphigh on " + internalid + " set to " + content["temphigh"]
					s0.write('{"content": { "variable":"AirTemperature.high", "value": "%s"}}' % int(content["temphigh"]))
				if "humlow" in content:
					print "humlow on " + internalid + " set to " + content["humlow"]
					s0.write('{"content": { "variable":"AirHumidity.low", "value": "%s"}}' % int(content["humlow"]))
				if "humhigh" in content:
					print "humhigh on " + internalid + " set to " + content["humhigh"]
					s0.write('{"content": { "variable":"AirHumidity.high", "value": "%s"}}' % int(content["humhigh"]))
				if "aircircint" in content:
					print "aircircint on " + internalid + " set to " + content["aircircint"]
					s0.write('{"content": { "variable":"AirCircInterval", "value": "%s"}}' % int(content["aircircint"]))

			except KeyError, e:
				print e

			#client.emitEvent(internalid, "event.device.state", "255", "")

		if content["command"] == "inventory":
			print "requesting inventory via " + internalid
			inventory()
			#client.emitEvent(internalid, "event.device.state", "0", "")

# specify our message handler method
client.addHandler(messageHandler)

client.addDevice("Controller", "controller")
client.addDevice("AirTemperatureValue", "binarysensor")
client.addDevice("AirHumidityValue", "binarysensor")

# then we add a background thread. This is not required and just shows how to send events from a separate thread. This might be handy when you have to poll something
# in the background or need to handle some other communication. If you don't need one or if you want to keep things simple at the moment just skip this section.

class mushroomEvent(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
    	level = 0
        while (True):
			line = s0.readline().rstrip()
			# check if json is valid
			try:
				message = json.loads(line)
			except ValueError, e:
				pass # invalid json
			else:
				message = json.loads(line)
				print(message)
				if "result" in message:
					if "inventory" in message['result']:
						sensors["AirTemperature"] = message['result']['inventory']['sensors']['AirTemperature']
						AirTemperatureValue = sensors["AirTemperature"]
						print "emitEvent AirTemperatureValue: " + str(AirTemperatureValue)
						client.emitEvent("AirTemperatureValue", "event.environment.temperaturechanged", AirTemperatureValue, "degC")

						sensors["AirHumidity"] = message['result']['inventory']['sensors']['AirHumidity']
						AirHumidityValue = sensors["AirHumidity"]
						print "emitEvent AirTemperatureValue: " + str(AirHumidityValue)
						client.emitEvent("AirHumidityValue", "event.environment.humiditychanged", AirHumidityValue, "percent")

				if "content" in message:
					if "event.environment.temperaturechanged" in message['subject']:
						sensors["AirTemperature"] = message['content']['level']
						AirTemperatureValue = sensors["AirTemperature"]
						print "emitEvent AirTemperatureValue: " + str(AirTemperatureValue)
						client.emitEvent("AirTemperatureValue", "event.environment.temperaturechanged", AirTemperatureValue, "degC")
					if "event.environment.humiditychanged" in message['subject']:
						sensors["AirHumidity"] = message['content']['level']
						AirHumidityValue = sensors["AirHumidity"]
						print "emitEvent AirHumidityValue: " + str(AirHumidityValue)
						client.emitEvent("AirHumidityValue", "event.environment.humiditychanged", AirHumidityValue, message['content']['unit'])
					if "event.environment.statechanged" in message['subject']:
						state["state"] = message['content']['state']
						print "emitEvent State change: " + str(state["state"])
						client.emitEvent("Controller", "event.environment.statechanged", state["state"], "state")

      
background = mushroomEvent()
background.setDaemon(True)
background.start()


# now you should have added all devices, set up all your internal and device specific stuff, started everything like listener threads or whatever. The call to run()
# is blocking and will start the message handling
client.run()

