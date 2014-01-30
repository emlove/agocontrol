#!/usr/bin/python
#################################################################
#
# Getting temperature data from temperatur.nu for ago control
#
# Developed by  Joakim Lindbom
#               (Joakim.Lindbom@gmail.com)
#               2014-01-11
#
AGO_TEMPERATURNU_VERSION = '0.0.3'
#
#################################################################
#
# To do: Get a list of stations, calculate average temp
#        (Optionaly only calculate average if distance to first
#         station is greater than e.g. 3 km)
# Check distance, if longer than e.g. 25 km, ignore value
#
#################################################################

import optparse
import logging, syslog
from lxml import etree
import urllib2
import threading
import sys, getopt, os, time
from qpid.log import enable, DEBUG, WARN
from qpid.messaging import Message
import agogeneral

import xml.etree.cElementTree as ET

import agoclient

debug = False
devId = "ex_temp"

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)

logging.basicConfig(filename='/var/log/temperaturnu.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO) #level=logging.DEBUG
#logging.setLevel( logging.INFO )

def info (text):
    logging.info (text)
    syslog.syslog(syslog.LOG_INFO, text)
    if debug:
        print "INF " + text + "\n"
def debug (text):
    logging.debug (text)
    syslog.syslog(syslog.LOG_DEBUG, text)
    if debug:
        print "DBG " + text + "\n"
def error (text):
    logging.error(text)
    syslog.syslog(syslog.LOG_ERR, text)
    if debug:
        print "ERR " + text + "\n"
def warning(text):
    logging.warning (text)
    syslog.syslog(syslog.LOG_WARNING, text)
    if debug:
        print "WRN " + text + "\n"


def getXML(parms):
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request('http://api.temperatur.nu/tnu_1.12.php?' + parms, None, headers)
    error = False
    temp = 0.0

    try:
        xml_file = urllib2.urlopen(req).read()

        xmldata = etree.fromstring(xml_file)

        for item in xmldata.xpath('/rss/channel/item'):
            if "Please Upgrade" in item.xpath("./title/text()")[0]:
                info ("Error: " + item.xpath("./title/text()")[0])
                error = True
                #raise error instead
            else:
                temp = item.xpath("./temp/text()")[0]
    except:
        info ("Error: unknown error")
        error = True

    return error, temp

class tempEvent(threading.Thread):
        def __init__(self,lat, lon, mailadress):
                self.lastTempC = -274.0
                self.lat = lat
                self.lon = lon
                self.mailadress = mailadress
                threading.Thread.__init__(self)
        def run(self):
                while (True):
                        req = "lat=" + self.lat + "&lon=" + self.lon + "&verbose&cli=agocontrol-(" + self.mailadress + ")"
                        err, tempCstr = getXML (req)
                        if err:
                            error ("Error received when calling temperatur.nu")
                        else:
                            tempC = float(tempCstr)
                            if tempC <> self.lastTempC:
                                self.lastTempC = tempC
                                if (TempUnits == 'f' or TempUnits == 'F'):
                                        tempF = 9.0/5.0 * tempC + 32.0
                                        client.emitEvent(devId, "event.environment.temperaturechanged", tempF, "degF")
                                else:
                                        client.emitEvent(devId, "event.environment.temperaturechanged", tempC, "degC")
                        time.sleep (readWaitTime)


info( "+------------------------------------------------------------")
info( "+ temperaturnu.py startup. Version=" + AGO_TEMPERATURNU_VERSION)
info( "+------------------------------------------------------------")

client = agoclient.AgoConnection("temperaturnu")
if (agoclient.getConfigOption("temperaturnu", "debug", "false").lower() == "true"):
    debug = True

lat = agoclient.getConfigOption("system","lat","0")
lon = agoclient.getConfigOption("system","lon","0")
mailadress = agoclient.getConfigOption("system","mailadress","none")
units = agoclient.getConfigOption("system","units","SI")

TempUnits = "C"
if units.lower() == "us":
    TempUnits = "F"

readWaitTime = int(agoclient.getConfigOption("temperaturnu","waittime","300"))

if readWaitTime < 300: #Used to guarantie minumum 5 minutes between API calls
    readWaitTime  = 300

client.addDevice(devId, "temperaturesensor")

background = tempEvent(lat,lon,mailadress)
background.setDaemon(True)
background.start()

client.run()
