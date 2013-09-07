import urllib
import urllib2
import json

url = 'http://192.168.80.2:8008/jsonrpc'
# values = '{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"inventory"}}, "id":1 }'
# values = '{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":1 }'
# values = '{"method":"message","params":{"content":{"command":"inventory"}},"id":1,"jsonrpc":"2.0"}'
# values = '[{"method":"message","params":{"content":{"command":"inventory"}},"id":null,"jsonrpc":"2.0"}, {"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":2 },{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}},{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":4 },{"method":"message","params":{"content":{"command":"inventory"}},"jsonrpc":"2.0"}]'
#values = '{"method":"message","params":{"content":{"command":"inventory"}},"id":1,"jsonrpc":"2.0"}'
#values = '{"method":"subscribe","id":1,"jsonrpc":"2.0"}'
# values = '{"method":"unsubscribe","params":{"uuid": "401ae021-aad3-431e-bff7-dc95549799b6"},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"getevent","params":{"uuid": "8ebb77e0-ad9a-4279-9d29-990af0f115c1"},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"unsubscribe","id":1,"jsonrpc":"2.0"}'
# req = urllib2.Request(url, values)
# response = urllib2.urlopen(req)
# print response.read()
# controller = '51f9c2d8-d761-47db-894a-ba5905435142'; # 457991c4-4d3e-4533-82dc-2da65e4b6f27
controller = '457991c4-4d3e-4533-82dc-2da65e4b6f27';

values = '{"method":"message","params":{"content":{"command":"test","uuid":"54fbbd47-c4e0-46b5-8a94-25e6381c2c35"}},"id":1,"jsonrpc":"2.0"}'
#print values
run = True
while (run):
	req = urllib2.Request(url, values)
	# response = urllib2.urlopen(req)
	response = urllib2.urlopen(req)
	retval = json.loads(response.read())
	if retval["result"]["result"]["hallo"] != "blah":
		run = False
		print "ERRORRRR"
