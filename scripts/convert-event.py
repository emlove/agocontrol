#!/usr/bin/python
import simplejson
import sys
import os
import pickle

eventmap = {}

# read persistent uuid mapping from file
try:
	eventmapfile = open("/etc/opt/agocontrol/events.pck","r")
	eventmap = pickle.load(eventmapfile)
	eventmapfile.close()
except IOError, e:
	print "error"

with open('/etc/opt/agocontrol/maps/eventmap.json' , 'w') as outfile:
	simplejson.dump(eventmap, outfile, indent='\t')
outfile.close()
