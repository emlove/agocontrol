import agoclient
client = agoclient.AgoConnection("test")
def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "test":
			retval = {}
			retval["hallo"] = "blah"
			return retval
	return {}
client.addHandler(messageHandler)
client.addDevice("123", "test")
client.run()

