#!/usr/bin/env python

import cgi
import json
import os
import re

print "Content-type: application/json\n"

data = cgi.FieldStorage()

if data.getfirst("devices"):
    pattern = re.compile("^([^.]+)\.html$")
    result = []
    for path, dirs, files in os.walk('../templates/devices'):
        for fn in files:
            match = pattern.findall(fn)
            if len(match) > 0:
                result.append(match[0])

    print json.dumps(result)
