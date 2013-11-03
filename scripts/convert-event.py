#!/usr/bin/python
import simplejson
import sys
import os
import pickle

import agoclient

eventmap = {}

# read persistent uuid mapping from file
try:
	eventmapfile = open(agoclient.CONFDIR + "/events.pck","r")
	eventmap = pickle.load(eventmapfile)
	eventmapfile.close()
except IOError, e:
	print "error"

with open(agoclient.CONFDIR + '/maps/eventmap.json' , 'w') as outfile:
	simplejson.dump(eventmap, outfile, indent='\t')
outfile.close()
