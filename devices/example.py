import agoclient

client = agoclient.AgoConnection("test")

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "on":
			print "switching on: " + internalid
			client.emitEvent(internalid, "event.device.state", "255", "")
		if content["command"] == "off":
			print "switching off: " + internalid
			client.emitEvent(internalid, "event.device.state", "0", "")



# print agoclient.getConfigOption("system", "broker", "localhost")
client.addDevice("123", "dimmer")
client.addDevice("124", "switch")
client.addHandler(messageHandler)

client.run()

