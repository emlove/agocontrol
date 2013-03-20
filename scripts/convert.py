#!/usr/bin/python
from xml.dom.minidom import parseString
import simplejson
import sys
import os

if len(sys.argv) < 2:
	sys.exit('Usage: %s <OZW zwcfg file>' % sys.argv[0])

if not os.path.exists(sys.argv[1]):
	sys.exit('ERROR: OZW config file %s was not found!' % sys.argv[1])

if os.path.exists('/etc/opt/agocontrol/uuidmap/zwave.json'):
	sys.exit('ERROR: Mapping file already exist!')

try:
	file = open(sys.argv[1],'r')
	data = file.read()
	file.close()
	dom = parseString(data)
except:
	sys.exit('ERROR: Cannot parse OZW config file %s!' % sys.argv[1])

uuidmap = {}
for node in dom.getElementsByTagName('Node'):
	try:
		nodeid = node.attributes["id"].value
		nodeuuid = node.attributes["name"].value
		uuidmap[nodeuuid] = "%s/1" % nodeid
	except KeyError, e:
		pass

with open('/etc/opt/agocontrol/uuidmap/zwave.json' , 'w') as outfile:
	simplejson.dump(uuidmap, outfile)
outfile.close()
