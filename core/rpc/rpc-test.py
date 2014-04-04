import urllib
import urllib2
import json

url = 'http://192.168.80.2:8008/jsonrpc'
# values = '{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"inventory"}}, "id":1 }'
# values = '{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":1 }'
# values = '{"method":"message","params":{"content":{"command":"inventory"}},"id":1,"jsonrpc":"2.0"}'
# values = '[{"method":"message","params":{"content":{"command":"inventory"}},"id":null,"jsonrpc":"2.0"}, {"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":2 },{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}},{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":4 },{"method":"message","params":{"content":{"command":"inventory"}},"jsonrpc":"2.0"}]'
values = '{"method":"message","params":{"content":{"command":"inventory"}},"id":1,"jsonrpc":"2.0"}'
#values = '{"method":"subscribe","id":1,"jsonrpc":"2.0"}'
# values = '{"method":"unsubscribe","params":{"uuid": "401ae021-aad3-431e-bff7-dc95549799b6"},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"getevent","params":{"uuid": "8ebb77e0-ad9a-4279-9d29-990af0f115c1"},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"unsubscribe","id":1,"jsonrpc":"2.0"}'
# req = urllib2.Request(url, values)
# response = urllib2.urlopen(req)
# print response.read()
# controller = '51f9c2d8-d761-47db-894a-ba5905435142'; # 457991c4-4d3e-4533-82dc-2da65e4b6f27
# controller = '457991c4-4d3e-4533-82dc-2da65e4b6f27';
controller = '42b9bbae-4457-483f-94bf-72c27e0b3c38';

values = '{"method":"message","params":{"content":{"command":"setscenario","uuid":"' + controller + '","scenariomap":{"1":{"command":"on","uuid":"c81a868e-e3da-418a-9f4e-fbfa30dfdcb9"},"2":{"command":"scenariosleep","delay":1},"3":{"command":"off","uuid":"c81a868e-e3da-418a-9f4e-fbfa30dfdcb9"}}}},"id":2,"jsonrpc":"2.0"}'
# values = '{"method":"message","params":{"content":{"command":"setscenario","uuid":"' + controller + '","scenariomap":{"1":{"command":"on","uuid":"c81a868e-e3da-418a-9f4e-fbfa30dfdcb9"},"2":{"command":"scenariosleep","delay":1},"3":{"command":"off","uuid":"c81a868e-e3da-418a-9f4e-fbfa30dfdcb9"}}}},"id":2,"jsonrpc":"2.0"}'
#print values

# uuid=79403b64-3bb5-482a-a7a6-c44eda724bc8 command=getzones

values = '{"method":"message","params":{"content":{"command":"getzones","uuid":"79403b64-3bb5-482a-a7a6-c44eda724bc8"}},"id":1,"jsonrpc":"2.0"}'
req = urllib2.Request(url, values)
response = urllib2.urlopen(req)
rawdata = response.read()
print rawdata
retval = json.loads(rawdata)
print retval
# scenario = retval['result']['scenario']
# print "created scenario:", scenario
# print "running getscenario:"
# values = '{"method":"message","params":{"content":{"command":"getscenario","uuid":"' + controller + '","scenario":"' + scenario + '"}},"id":1,"jsonrpc":"2.0"}'
# print values
# req = urllib2.Request(url, values)
# response = urllib2.urlopen(req)
# print response.read()
# print "deleting scenario"
# values = '{"method":"message","params":{"content":{"command":"delscenario","uuid":"' + controller + '","scenario":"' + scenario +'"}},"id":3,"jsonrpc":"2.0"}'
# print values
# req = urllib2.Request(url, values)
# response = urllib2.urlopen(req)
# print response.read()
