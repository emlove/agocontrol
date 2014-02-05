#!/usr/bin/python
import simplejson
import sys
import os
import pickle

import agoclient

scenariomap = {}

# read persistent uuid mapping from file
try:
	scenariomapfile = open(agoclient.CONFDIR + "/scenarios.pck","r")
	scenariomap = pickle.load(scenariomapfile)
	scenariomapfile.close()
except IOError, e:
	print "error"

with open(agoclient.CONFDIR + '/maps/scenariomap.json' , 'w') as outfile:
	simplejson.dump(scenariomap, outfile, indent='\t')
outfile.close()
