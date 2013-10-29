'''
	AGOControl Event Engine for XBMC
	Copyright (C) 2013 Jeroen Simonetti

	LICENSE:
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 2 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
   
	DESCRIPTION:
	This XBMC addon sends events from xbmc player status into agocontrol.
   
	WRITTEN:	01/2013
'''

# CONSTANTS
__author__ = 'Jeroen Simonetti'
__version__ = '0.1.0'
__url__ = 'https://www.agocontrol.com/'

# imports
# system
import sys
# xbmc
import xbmcaddon

# fetch addon information
agoevents = xbmcaddon.Addon('script.agoevents')

# add libraries to path
library_path = agoevents.getAddonInfo('path') + '/resources/Lib/'
sys.path.append(library_path)

# custom imports
import ConfigParser
from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

import events

import agoclient

xevent = events.xbmcEvents()

opts = {}
opts = ConfigParser.ConfigParser()
opts.read(agoclient.CONFDIR + '/config.ini')

#try:
#	opts.username = agoevents.getSetting('broker_username')
#except:
opts.username = "agocontrol"

#try:
#	opts.password = agoevents.getSetting('broker_password')
#except:
opts.password = "letmein"

#try:
#	broker = agoevents.getSetting('broker_host')
#except:
broker = "localhost"

#try:
#	debug = agoevents.getSetting('debug')
#except:
debug = "WARN"

if debug=="DEBUG":
	enable("qpid", DEBUG)
else:
	enable("qpid", WARN)
 
opts.reconnect = True

xevent.connection = Connection(broker, username=opts.username, password=opts.password, reconnect=True)

try:
	xevent.connection.open()
	xevent.session = xevent.connection.session()
	# we use the command topic exchange
	xevent.sender = xevent.session.sender("agocontrol; {create: always, node: {type: topic}}")
	xevent.RunMainLoop(0.5)
except SendError, e:
	print e

xevent.connection.close()

