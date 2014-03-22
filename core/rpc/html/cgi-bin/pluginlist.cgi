#!/usr/bin/env python

import cgi
import json
import os

print "Content-type: application/json\n"

result = []

for path, dirs, files in os.walk('../plugins/'):
	for fn in files:
		if fn == "metadata.json":
			try:
				with open(path + "/" + fn) as data:
					content = data.read()
					obj = json.loads(content)
					obj["_name"] = os.path.basename(path)
					result.append(obj)
			except Exception as error:
				pass

print json.dumps(result)
