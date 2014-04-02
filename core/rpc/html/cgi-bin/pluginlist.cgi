#!/usr/bin/env python

import cgi
import json
import os

print "Content-type: application/json\n"

plugins = {}
result = []

for path, dirs, files in os.walk('../plugins/'):
	for fn in files:
		if fn == "metadata.json":
			try:
				with open(path + "/" + fn) as data:
					content = data.read()
					obj = json.loads(content)
					obj["_name"] = os.path.basename(path)
					plugins[obj["_name"]] = obj
			except Exception as error:
				pass
for key in sorted(plugins.iterkeys()):
	result.append(plugins[key])
print json.dumps(result)
