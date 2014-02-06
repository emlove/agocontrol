#!/usr/bin/python
AGO_WEATHERREPORTER_VERSION = '0.0.1'
############################################
"""
Weather reporing support for ago control
Uploading temperature and humidity to crowd sourced weather data sites

"""
__author__     = "Joakim Lindbom"
__copyright__  = "Copyright 2014, Joakim Lindbom"
__date__       = "2013-01-31"
__credits__    = ["Joakim Lindbom", "The ago control team"]
__license__    = "GPL Public License Version 3"
__maintainer__ = "Joakim Lindbom"
__email__      = 'Joakim.Lindbom@gmail.com'
__status__     = "Experimental"
__version__    = AGO_WEATHERREPORTER_VERSION
############################################

#import optparse
import sys, syslog, logging
#import time
from datetime import date, datetime
#from qpid.log import enable, DEBUG, WARN
import threading
#from qpid.messaging import Message
#import agogeneral
#from configobj import ConfigObj
#import httplib, urllib, urllib2
import requests
import ConfigParser, os
from configobj import ConfigObj
import json

from qpid.messaging import *
#from qpid.util import URL
from qpid.log import enable, DEBUG, WARN


from threading import Timer
import time, sys

#import agoclient

config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
    username = config.get("system", "username")
except:
    username = "agocontrol"

try:
    password = config.get("system", "password")
except:
    password = "letmein"

try:
    broker = config.get("system", "broker")
except:
    broker = "localhost"

temperaturenu_lock = threading.Lock()
weatherunderground_lock = threading.Lock()

try:
    debug = config.get("system", "debug")
except:
    debug = "WARN"

if debug == "DEBUG":
    enable("qpid", DEBUG)
else:
    enable("qpid", WARN)

def info (text):
    #logging.info (text)
    syslog.syslog(syslog.LOG_INFO, text)
    if debug:
        print "INF " + text + "\n"
def debug (text):
    #logging.debug (text)
    syslog.syslog(syslog.LOG_DEBUG, text)
    if debug:
        print "DBG " + text + "\n"
def error (text):
    #logging.error(text)
    syslog.syslog(syslog.LOG_ERR, text)
    if debug:
        print "ERR " + text + "\n"
def warning(text):
    #logging.warning (text)
    syslog.syslog(syslog.LOG_WARNING, text)
    if debug:
        print "WRN " + text + "\n"


info( "+------------------------------------------------------------")
info( "+ agoweathereporter.py startup. Version=" + AGO_WEATHERREPORTER_VERSION)
info( "+------------------------------------------------------------")


def parseLine(dataIn):
    """ Check the message contains relevant data. If so, reformat into JSON format and unpack
    """
    data = str(dataIn)
    ret = {}

    if "event.environment.temperaturechanged" in data or "event.environment.humiditychanged" in data:
        content2 = '{ "content": ' + data[data.find("content")+8:len(data)-1] + ' }'
        content3 = content2.replace("u\'", '\"')  # check if this is necessary!
        content4 = content3.replace("\'", '\"')

        js = json.loads(content4)
        ret["uuid"] = js["content"]["uuid"]
        ret["units"] = js["content"]["unit"]
        ret["level"] = js["content"]["level"]

    return ret

def sendTemperaturNu(temp, reporthash):
    """ Send temperature data to http://temperatur.nu
    """
    #print time.strftime("%H:%M:%S", time.gmtime()) + " temperatur.nu reporting temp=" +str(temp)+ " for UUID=" + reporthash
    info ("temperatur.nu reporting temp=" +str(temp)+ " for UUID=" + reporthash)
    # params = urllib.urlencode({'hash': reporthash, 't': str(temp)})
    # headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    # conn = httplib.HTTPConnection("www.temperatur.nu")
    # conn.request("POST", "/rapportera.php", params, headers)
    # response = conn.getresponse()
    # data = response.read()
    #conn.close()

    #if response.status == 200 and response.reason == "OK" and "ok!" in data:

    # Critical section, don't want two of these running at the same time
    with temperaturenu_lock:
        r = requests.get('http://www.temperatur.nu/rapportera.php?hash=' + reporthash + '&t=' + str(temp))
        status = r.status_code
        data = r.text

        if r.status_code == 200 and "ok! (" in data and len(data) > 6:
            return True
        else:
            error("something went wrong when reporting. response=" + data)
            # Some logging needed here
            return False

def sendWeatherUnderground(stationid, password, temp, tempUnit):
    if tempUnit == "degC":
        tempstr = 'tempc'
        #tempF = float(temp)*9/5+32
    else:
        tempstr = 'tempf'
        #tempF = float(temp)

    data = {
        'ID': stationid,
        'PASSWORD': password,
        'dateutc': str(datetime.utcnow()),
        tempstr: str(temp),
        'action': 'updateraw',
        'softwaretype': 'ago control',
        'realtime': '1',
        'rtfreq': '2.5'
    }
    url = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'

    r = requests.post(url=url, data=data)

    #Raise exception if status code is not 200
    r.raise_for_status()
    if r.text == 'success\n':
        return True
    else:
        print "something went wrong when reporting. response=" + r.text
        # Some logging needed here
        return False

class reportThread(threading.Thread):
    """ Some weather sites need to get updated frequently in order to accept the data.
        This thread sends data on a defined interval
    """
    def __init__(self,):
        threading.Thread.__init__(self)
        self.delay = 20 # general_delay
    def run(self):
        while (True):
            time.sleep (self.delay) #general_delay or service specific
            for s, val in sensors.iteritems():
                if val['service'] == "temperatur.nu" and val['temp'] != -274:
                    sendTemperaturNu(str(val["temp"]), val["hash"])
                    self.delay = val["delay"]


# route stderr to syslog
class LogErr:
    def write(self, data):
        syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
sys.stderr = LogErr()

config = ConfigObj("/etc/opt/agocontrol/conf.d/weatherreporter.conf")
general_delay = 120

section = config['Services']
sensors = {}
for y in section:
    s = {}
    if "Delay" in y:
        general_delay = float(config['Services']['Delay'])
    else:
        s['service'] = y

        sensorsection = config['Services'][y]
        for sens in sensorsection:
            t = {}
            t["service"] = y
            t["name"] = sens
            try:
                t['delay'] = config['Services'][y]['Delay']
            except KeyError:
                t['delay'] = general_delay

            try:
                t['hash'] = sensorsection[sens]['Hash']
            except KeyError:
                if y == "temperatur.nu":
                    error ("Hash value is mandatory for temperatur.nu. Cannot continue")
                    sys.exit()
            try:
                t['device'] = config['Services'][y][sens]['Sensor']   # devId or UUID??!?
            except KeyError:
                error("Cannot continue without knowing which sensor to report.")
                sys.exit()
            try:
                t['uuid'] = config['Services'][y][sens]['UUID']   #
            except KeyError:
                error("Cannot continue without knowing UUID of sensor")
                sys.exit()
            t["temp"] = -274
            sensors[t['device']] = t

connection = Connection(broker, username=username, password=password, reconnect=True)
#try:
background = reportThread()
background.setDaemon(True)
background.start()

connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
receiver.capacity=100
while True:
    try:
        message = receiver.fetch()
        #message  = "subject=u'event.environment.temperaturechanged', properties={u'qpid.subject': u'event.environment.temperaturechanged', 'x-amqp-0-10.routing-key': u'event.environment.temperaturechanged'}, content={u'uuid': u'03f2f1d7-41c2-4fbc-a0d9-7656e8122e28', u'unit': u'degC', u'level': u'-2.8'})"
        #print message
    except Empty:
        print "Empty"
        message = None

    if message.subject is not None:
        if "event.environment.temperaturechanged" in message.subject or "event.environment.humiditychanged" in message.subject:
            res = parseLine(message)
            #print message.content["level"] + " " + message.content["unit"] + " " + message.content["uuid"]

            if len(res) > 0:
                #print "Reported " + str(res["level"]) + " " + str(res["units"])
                uuid = res["uuid"]
                for x in sensors:
                    if uuid == sensors[x]["uuid"] and res["units"] == "degC":
                        sensors[x]["temp"] = float(res["level"])
                        #print time.strftime("%H:%M:%S", time.gmtime()) + " new temp for device=" + sensors[x]["device"] + " temp=" + str(sensors[x]["temp"])
                        info("New temp for device=" + sensors[x]["device"] + " temp=" + str(sensors[x]["temp"]))
                        #sendTemperaturNu(str(res["level"]))
                        sendTemperaturNu(sensors[x]["temp"], sensors[x]["hash"])
                        send

    session.acknowledge()
# End while True

#except SendError, e:
#    print "SendError " + e
#except ReceiverError, e:
#    print "ReceiverError " + e
#except KeyboardInterrupt:
#    print "keyb"
#finally:
print "z"
connection.close()
