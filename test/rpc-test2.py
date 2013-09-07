import urllib
import urllib2
import json

url = 'http://192.168.80.2:8008/jsonrpc'
values = '{"method":"message","params":{"content":{"command":"test","uuid":"54fbbd47-c4e0-46b5-8a94-25e6381c2c35"}},"id":1,"jsonrpc":"2.0"}'

run = True
while (run):
	req = urllib2.Request(url, values)
	# response = urllib2.urlopen(req)
	response = urllib2.urlopen(req)
	retval = json.loads(response.read())
	if retval["result"]["result"]["hallo"] != "blah":
		run = False
		print "ERRORRRR"
