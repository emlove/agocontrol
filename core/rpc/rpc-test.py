import urllib
import urllib2

url = 'http://127.0.0.1:8008/jsonrpc'
# values = '{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"inventory"}}, "id":1 }'
# values = '{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":1 }'
values = '{"method":"message","params":{"content":{"command":"inventory"}},"id":1,"jsonrpc":"2.0"}'
# values = '[{"method":"message","params":{"content":{"command":"inventory"}},"id":null,"jsonrpc":"2.0"}, {"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":2 },{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}},{"jsonrpc" : "2.0", "method" : "message", "params" : {"content":{"command":"off", "uuid":"0962f27e-99ce-43a4-872b-97d75d61f464"}}, "id":4 },{"method":"message","params":{"content":{"command":"inventory"}},"jsonrpc":"2.0"}]'
# values = '{"method":"message","params":{"content":{"command":"inventory"}},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"subscribe","id":1,"jsonrpc":"2.0"}'
# values = '{"method":"unsubscribe","params":{"uuid": "401ae021-aad3-431e-bff7-dc95549799b6"},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"getevent","params":{"uuid": "2d28cb85-5be0-4ccb-bc21-33bf94ed04ec"},"id":1,"jsonrpc":"2.0"}'
# values = '{"method":"unsubscribe","id":1,"jsonrpc":"2.0"}'
req = urllib2.Request(url, values)
response = urllib2.urlopen(req)
print response.read()
