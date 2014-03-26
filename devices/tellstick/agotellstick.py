#!/usr/bin/python
AGO_TELLSTICK_VERSION = '0.0.9'
############################################
#
# Tellstick Duo support for ago control
#
__author__     = "Joakim Lindbom"
__copyright__  = "Copyright 2013, 2014, Joakim Lindbom"
__date__       = "2013-12-24"
__credits__    = ["Joakim Lindbom", "The ago control team"]
__license__    = "GPL Public License Version 3"
__maintainer__ = "Joakim Lindbom"
__email__      = 'Joakim.Lindbom@gmail.com'
__status__     = "Experimental"
__version__    = AGO_TELLSTICK_VERSION
############################################

import optparse
import logging
import sys
import syslog
import time
from qpid.log import enable, DEBUG, WARN
from qpid.messaging import Message
from configobj import ConfigObj

from threading import Timer
import time

import agoclient

#debug = False
debug = True

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)

logging.basicConfig(filename='/var/log/tellstick.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO) #level=logging.DEBUG
#logging.setLevel( logging.INFO )

timers = {} # List of timers
event_received = {}
lasttime = {}
dev_delay = {}
sensors = {}



def info (text):
    logging.info (text)
    #syslog.syslog(syslog.LOG_INFO, text)
    if debug:
        print ("INF " + text + "\n")
def debug (text):
    logging.debug (text)
    syslog.syslog(syslog.LOG_DEBUG, text)
    if debug:
        print ("DBG " + text + "\n")
def error (text):
    logging.error(text)
    syslog.syslog(syslog.LOG_ERR, text)
    if debug:
        print ("ERR " + text + "\n")
def warning(text):
    logging.warning (text)
    syslog.syslog(syslog.LOG_WARNING, text)
    if debug:
        print ("WRN " + text + "\n")

def messageHandler(internalid, content):
    if "command" in content:
        #
        #   On
        #
        if content["command"] == "on":
            resCode = t.turnOn(internalid)
            if resCode != 'success':   # != 0:
                print "rescode=" + resCode
                #res = t.getErrorString(resCode)
                error("tellstick.py error turning on device. res=" + resCode)
            else:
                client.emitEvent(internalid, "event.device.statechanged", "255", "")
            if debug:
                info("Turning on device:  " + str(internalid) + " res=" + resCode)

        #
        #   Allon - will require changes in schema.yaml + somewhere else too
        #
        if content["command"] == "allon":
            if debug:
                info("Command 'allon' received")

        #
        #   Off
        #
        if content["command"] == "off":
            resCode = t.turnOff(internalid)
            if resCode != 'success':  # 0:
                #res = t.getErrorString(resCode)
                error("tellstick.py error turning off device. res=" + resCode)
            else:
                #res = 'Success'
                client.emitEvent(internalid, "event.device.statechanged", "0", "")
            if debug:
                info("Turning off device: " + str(internalid) + " res="+ resCode)

        #
        #   Setlevel for dimmer
        #
        if content["command"] == "setlevel":
            resCode = t.dim(internalid, int(255 * int(content["level"]))/100)  # Different scales: aGo use 0-100, Tellstick use 0-255
            if resCode != 'success':  # 0:
                error( "tellstick.py error dimming device. res=" + resCode)
            else:
                #res = 'Success'
                client.emitEvent(internalid, "event.device.statechanged", content["level"], "")

            if debug:
                info("Dimming device=" + str(internalid) + " res=" + resCode + " level=" + str(content["level"]))

#Event handlers for device and sensor events
def agoDeviceEvent(deviceId, method, data, callbackId):
    global event_received, lasttime, dev_delay, general_delay
    print "agoDeviceEvent devId=" + str(deviceId)

    received = event_received.get(deviceId)
    if received == None:
        received = event_received[deviceId] = 0
        lasttime[deviceId] = time.time()

    if debug:
        info ("time-lasttime=" + str(time.time() - lasttime[deviceId]))

    if received == 1:
        delay = dev_delay.get(deviceId)
        if delay == None:
            delay = general_delay

        if (time.time() - lasttime[deviceId]) > delay:
            #No echo, stop cancelling events
            received = event_received[deviceId] = 0
        else:
            info ("Echo cancelled")

    if received == 0:
        #if debug:
            #info('%d: DeviceEvent Device: %d - %s  method: %s, data: %s' %(time.time(), deviceId, t.getName(deviceId), t.methodsReadable.get(method, 'Unknown'), data))

        received = event_received[deviceId] = 1
        lasttime[deviceId] = time.time()

        #print "method=" + str(method)
        if (method == t.TELLSTICK_TURNON):
            client.emitEvent(deviceId, "event.device.statechanged", "255", "")
            if debug:
                info ("emitEvent statechanged " + str(deviceId) + " ON 255")

        if (method == t.TELLSTICK_TURNOFF):
            client.emitEvent(deviceId, "event.device.statechanged", "0", "")
            if debug:
                info ("emitEvent statechanged " + str(deviceId) + " OFF 0")
        # if (method == t.TELLSTICK_DIM): #Hmm, not sure if this can happen?!?
        #     level = int(100 * int(data))/255
        #     if int(data) > 0 and int(data) < 255:
        #         level = level +1
        #     client.emitEvent(deviceId, "event.device.statechanged", str(level), "")
        #     if debug:
        #         info ("emitEvent statechanged DIM " + str(level))


#def agoDeviceChangeEvent(deviceId, changeEvent, changeType, callbackId):
#    if debug:
#        print ('%d: DeviceChangeEvent Device: %d - %s' %(time.time(), deviceId, t.getName(deviceId)))
#        print ('  changeEvent: %d' %( changeEvent ))
#        print ('  changeType: %d' %( changeType ))


#def agoRawDeviceEvent(data, controllerId, callbackId):
#    if debug:
#        print ('%d: RawDeviceEvent: %s - controllerId: %s' %(time.time(), data, controllerId))
#    if 'class:command' in str(data):
#        protocol = data.split(";")[1].split(":")[1]
#        print ("protocol=" + protocol)
#
#        if "arctech" or "waveman" in protocol:
#            house = data.split(";")[3].split(":")[1]
#            unit = data.split(";")[4].split(":")[1]
#            devID = "SW" + house+unit
#            print ("devid=", devID)
#            method = data.split(";")[5].split(":")[1]
#            print ("method=" + method)
#
#        if "sartano" in protocol:
#            code = data.split(";")[3].split(":")[1]
#            devID = "SW" + code
#            print ("devid=", devID)
#            method = data.split(";")[4].split(":")[1]
#            print ("method=" + method)

def emitTempChanged(devId, temp):
    global sensors
    tempC = temp
    if TempUnits == 'F':
        tempF = 9.0/5.0 * tempC + 32.0
        if tempF != float(sensors[devId]["lastTemp"]):
            sensors[devId]["lastTemp"] = tempF
            client.emitEvent(devId, "event.environment.temperaturechanged", str(tempF), "degF")
    else:
        #print "devId=" + str(devId)
        if tempC != float(sensors[devId]["lastTemp"]):
            sensors[devId]["lastTemp"] = tempC
            client.emitEvent(devId, "event.environment.temperaturechanged", str(tempC), "degC")

def emitHumidityChanged(devId, humidity):
    global sensors
    #print "hum=" + str(humidity)
    #print "last=" + str(sensors[devId]["lastHumidity"])

    if humidity != float(sensors[devId]["lastHumidity"]):
        sensors[devId]["lastHumidity"] = humidity
        client.emitEvent(devId, "event.environment.humiditychanged", str(humidity), "%")

def listNewSensors():
    global sensors
    sensors = t.listSensors()
    for id, value in sensors.iteritems():
        if value["new"] == True:
            value["new"] = False
            devId = str(id)
            if value["isMultiLevel"]:
                client.addDevice (devId, "multilevelsensor")
                if value["isTempSensor"]:
                    emitTempChanged(devId, float(value["temp"]))
                if value["isHumiditySensor"]:
                    emitHumidityChanged(devId, float(value["humidity"]))

            else:
                if value["isTempSensor"]:
                    client.addDevice(devId, "temperaturesensor")
                    emitTempChanged(devId, float(value["temp"]))

                if value["isHumiditySensor"]:
                    client.addDevice (devId, "multilevelsensor")
                    emitHumidityChanged(devId, float(value["humidity"]))

def reportSensorEvent(deviceId): #Add SensorData to parameters
    if debug:
        info ("Reporting sensor event")
    #client.emitEvent(deviceId, "event.device.statechanged", "255", "") # Wrong event, check which to use for a sensor

def agoSensorEvent(protocol, model, id, dataType, value, timestamp, callbackId):
    global sensors
    print "SensorEvent called for " + str(id)
    #print '%d: SensorEvent' %(time.time())
    #print '  protocol: %s' %(protocol)
    #print '  model: %s' %(model)
    #print '  id: %s' %(id)
    #print '  dataType: %d' %(dataType)
    #print '  value: %s' %(value)
    #print '  timestamp: %d' %(timestamp)

    listNewSensors()
    devId = str(id)
    if "temp" in model and dataType & t.TELLSTICK_TEMPERATURE == t.TELLSTICK_TEMPERATURE:
        emitTempChanged(devId, float(value))
        # tempC = value
        # if TempUnits == 'F':
        #     tempF = 9.0/5.0 * tempC + 32.0
        #     client.emitEvent(str(devId), "event.environment.temperaturechanged", tempF, "degF")
        # else:
        #     client.emitEvent(str(devId), "event.environment.temperaturechanged", tempC, "degC")
    if "humidity" in model and dataType & t.TELLSTICK_HUMIDITY == t.TELLSTICK_HUMIDITY:
        emitHumidityChanged(devId, float(value))
        #client.emitEvent(str(devId), "event.environment.humiditychanged", float(value), "%")


info( "+------------------------------------------------------------")
info( "+ Tellstick.py startup. Version=" + AGO_TELLSTICK_VERSION)
info( "+------------------------------------------------------------")

client = agoclient.AgoConnection("tellstick")
#device = (agoclient.getConfigOption("tellstick", "device", "/dev/usbxxxx")
if (agoclient.getConfigOption("tellstick", "debug", "false").lower() == "true"):
    debug = True

config = ConfigObj("/etc/opt/agocontrol/conf.d/tellstick.conf")
#config = ConfigObj("./tellstick.conf")
try:
    general_delay = float(config['EventDevices']['Delay'])/1000
except:
    general_delay = 0.5
#section = config['EventDevices']

SensorPollDelay = 300.0  # 5 minutes
try:
    if 'SensorPollDelay' in config['tellstick']:
        SensorPollDelay = config['tellstick']['SensorPollDelay']
except KeyError:
    pass


units = agoclient.getConfigOption("system", "units", "SI")
TempUnits = "C"
if units.lower() == "us":
    TempUnits = "F"

try:
    stickVersion = config['tellstick']['StickVersion']
except:
    stickVersion = "Tellstick Dou"

if "Net" in stickVersion:
    # Postpone tellsticknet loading, has extra dependencies which
    # we can do without if we've only got a Duo
    from tellsticknet import tellsticknet
    t = tellsticknet()
else:
    from  tellstickduo import  tellstickduo
    t = tellstickduo()

t.init(SensorPollDelay, TempUnits)

client.addHandler(messageHandler)

# Get inventory, required to set names on new devices
inventory = client.getInventory().content
agoController = None
for uuid in inventory['devices'].keys():
    d = inventory['devices'][uuid]
    if d['devicetype'] == 'agocontroller':
        agoController = uuid
        break

if agoController == None:
    warning("No agocontroller found, cannot set device names")
else:
    info("agoController found: " + agoController)


def setNameIfNecessary(deviceUUID, name):
    dev = inventory['devices'].get(deviceUUID)
    if (dev == None or dev['name'] == '') and name != '':
        content = {}
        content["command"] = "setdevicename"
        content["uuid"] = agoController
        content["device"] = deviceUUID
        content["name"] = name
        message = Message(content=content)
        client.sendMessage (None, content)
        info ("'setdevicename' message sent. name=" + name)

# Get devices from Telldus, announce to Ago Control
info("---Getting switches and dimmers---")
switches = t.listSwitches()
for devId, dev in switches.iteritems():
#    devId = t.getDeviceId(i)
#    model = t.getModel(devId)
#    name = t.getName(devId)
    model = dev["model"]
    name = dev["name"]

    info("devId=" + str(devId) + " name=" + name + " model=" + model)
    #+ " method=" + t.methods(devId))

    #found = False
    deviceUUID = ""

    #if ("selflearning-switch" in model or model == "switch"):
    if dev["isDimmer"]:
        client.addDevice(devId, "dimmer")
    else:
        client.addDevice(devId, "switch")

    deviceUUID = client.internalIdToUuid (devId)
    #info ("deviceUUID=" + deviceUUID + " name=" + t.getName(devId))
    #info("Switch Name=" + dev.name + " protocol=" + dev.protocol + " model=" + dev.model)
    #if ("selflearning-dimmer" in model or model == "dimmer"):

    # Check if device already exist, if not - send its name from the tellstick config file
    setNameIfNecessary(deviceUUID, name)

info("---Getting remotes & motion sensors---")
remotes = t.listRemotes()
for devId, dev in remotes.iteritems():
    model = dev["model"]
    name = dev["name"]
    info("devId=" + str(devId) + " name=" + name + " model=" + model)

    if not "codeswitch" in model:
        client.addDevice(devId, "binarysensor")
        deviceUUID = client.internalIdToUuid (devId)

        #found = True
        "devId=" + str(devId) + " model " + model
        try:
            dev_delay[devId] = float(config['EventDevices'][str(devId)]['Delay'])/1000
        except KeyError:
            dev_delay[devId] = general_delay

        # Check if device already exist, if not - send its name from the tellstick config file
        setNameIfNecessary(deviceUUID, name)

info("---Getting temp and humidity sensors---")
listNewSensors()

#
#  Register event handlers
#
cbId = []

cbId.append(t.registerDeviceEvent(agoDeviceEvent))
info('Register device event returned:' + str(cbId[-1]))

#cbId.append(t.registerDeviceChangedEvent(agoDeviceChangeEvent))
#info ('Register device changed event returned:' + str(cbId[-1]))

#cbId.append(t.registerRawDeviceEvent(agoRawDeviceEvent))
#info ('Register raw device event returned:' + str(cbId[-1]))

cbId.append(t.registerSensorEvent(agoSensorEvent))
info('Register sensor event returned:' + str(cbId[-1]))

client.run()

t.close()
