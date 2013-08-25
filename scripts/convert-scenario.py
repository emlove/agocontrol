#!/usr/bin/python
import simplejson
import sys
import os
import pickle

scenariomap = {}

# read persistent uuid mapping from file
try:
	scenariomapfile = open("/etc/opt/agocontrol/scenarios.pck","r")
	scenariomap = pickle.load(scenariomapfile)
	scenariomapfile.close()
except IOError, e:
	print "error"

with open('/etc/opt/agocontrol/scenariomap.json' , 'w') as outfile:
	simplejson.dump(scenariomap, outfile, indent='\t')
outfile.close()
