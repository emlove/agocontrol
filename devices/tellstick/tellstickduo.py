#!/usr/bin/python
AGO_TELLSTICK_VERSION = '0.0.9'
"""
############################################
#
# Tellstick Duo class
#
# Date of origin: 2014-01-25
#
__author__     = "Joakim Lindbom"
__copyright__  = "Copyright 2014, Joakim Lindbom"
__credits__    = ["Joakim Lindbom", "The ago control team"]
__license__    = "GPL Public License Version 3"
__maintainer__ = "Joakim Lindbom"
__email__      = 'Joakim.Lindbom@gmail.com'
__status__     = "Experimental"
__version__    = AGO_TELLSTICK_VERSION
############################################
"""
from tellstickbase import tellstickbase
import td

class tellstickduo(tellstickbase):
    """Class used for Tellstick & Tellstick Duo devices"""
    def __init__(self):
        self.TELLSTICK_TURNON = 1
        self.TELLSTICK_TURNOFF = 2
        self.TELLSTICK_BELL = 4
        self.TELLSTICK_DIM = 16
        self.TELLSTICK_UP = 128
        self.TELLSTICK_DOWN = 256

        self.TELLSTICK_TEMPERATURE = td.TELLSTICK_TEMPERATURE
        self.TELLSTICK_HUMIDITY = td.TELLSTICK_HUMIDITY
        self.sensors={}
        self.switches={}
        self.remotes={}
        #super(tellstickduo, self).__init__() # call base class init method

    def __get__(self, obj, objtype=None):
        pass

    def __set__(self, obj, val):
        pass

    def __delete__(self, obj):
        pass

    def init(self, SensorPollDelay, TempUnits):
        #TELLSTICK_BELL | TELLSTICK_TOGGLE | TELLSTICK_LEARN | TELLSTICK_EXECUTE | TELLSTICK_UP | TELLSTICK_DOWN | TELLSTICK_STOP
        td.init( defaultMethods = td.TELLSTICK_TURNON | td.TELLSTICK_TURNOFF | td.TELLSTICK_DIM)

    def close(self):
        return td.close()

    def turnOn(self, devId):
        resCode = td.turnOn(devId)
        return self.getErrorString(resCode).lower()

    def turnOff(self, devId):
        resCode =  td.turnOff(devId)
        return self.getErrorString(resCode).lower()

    def getErrorString(self, resCode):
        return td.getErrorString(resCode)

    def dim(self, devId, level):
        resCode = td.dim(devId, level)
        return self.getErrorString(resCode).lower()

    def getName(self,devId):
        return td.getName(devId)

    def methodsReadable(self, method, default):
        return td.methodsReadable(method, default)

    def getNumberOfDevices(self):
        return td.getNumberOfDevices()

    def getNumberOfSensors(self):
        return td.getNumberOfDevices() #wrong


    def getDeviceId(self,i):
        return td.getDeviceId(i)

    def getModel(self, devId):
        return td.getModel(devId)

    def registerDeviceEvent(self, deviceEvent):
        return td.registerDeviceEvent(deviceEvent)

    def registerDeviceChangedEvent(self, deviceEvent):
        return td.registerDeviceChangedEvent(deviceEvent)

    def SensorEventInterceptor (self, protocol, model, id, dataType, value, timestamp, callbackId):
        devId = "S" + str(id)
        print "SensorEventInterceptod called for " + devId

        if devId not in self.sensors:
            s = {}
            s["id"] =devId
            s["model"]= model
            #print("New sensor intercepted: devId=" + s["id"] + " model=" + model)
            s["new"] = True
            if dataType & td.TELLSTICK_TEMPERATURE == td.TELLSTICK_TEMPERATURE:
                s["temp"] = float(value) # C/F
                s["lastTemp"] = float(-274.0)
                s["isTempSensor"] = True
            else:
                s["isTempSensor"] = False
            if dataType & td.TELLSTICK_HUMIDITY == td.TELLSTICK_HUMIDITY:
                s["humidity"] = float(value)
                s["lastHumidity"] = float(-999.0)
                s["isHumiditySensor"] = True
            else:
                s["isHumiditySensor"] = False
            if "temp" in s and "humidity" in s:
                s["isMultiLevel"] = True
            else:
                s["isMultiLevel"] = False
            self.sensors[devId] = s


        if devId in self.sensors:
            s = self.sensors[devId]
            if (dataType & td.TELLSTICK_HUMIDITY == td.TELLSTICK_HUMIDITY and s["isHumiditySensor"] == False) or (dataType & td.TELLSTICK_TEMPERATURE == td.TELLSTICK_TEMPERATURE and s["isTempSensor"] == False):
                print("New data type intercepted: devId=" + devId + " model=" + model)
                s["new"] = True
                if dataType & td.TELLSTICK_TEMPERATURE == td.TELLSTICK_TEMPERATURE:
                    s["temp"] = float(value)  # C/F
                    s["lastTemp"] = float(-274.0)
                    s["isTempSensor"] = True
                    if "humidity" in s:
                        s["isMultiLevel"] = True

                if dataType & td.TELLSTICK_HUMIDITY == td.TELLSTICK_HUMIDITY:
                    s["humidity"] = float(value)
                    s["lastHumidity"] = float(-999.0)
                    s["isHumiditySensor"] = True
                    if "temp" in s:
                        s["isMultiLevel"] = True
                self.sensors[devId] = s

        # Call registered callback
        self.SensorEvent(protocol, model, devId, dataType, value, timestamp, callbackId)

    def registerSensorEvent(self, deviceEvent):
        self.SensorEvent = deviceEvent
        return td.registerSensorEvent(self.SensorEventInterceptor)

    def listSensors(self):
        if len(self.sensors) == 0:
            self.sensors = td.listSensors()

        return self.sensors


    def listSwitches(self):
        if len(self.switches) == 0:

            for i in range(self.getNumberOfDevices()):
                devId = self.getDeviceId(i)
                model = self.getModel(devId)

                if ('switch' in model or 'dimmer' in model):
                    dev = {}
                    dev["id"] = devId
                    dev["name"] = self.getName(devId)
                    dev["model"] = model
                    if 'dimmer' in model:
                        dev["isDimmer"] = True
                    else:
                        dev["isDimmer"] = False

                    self.switches[devId] = dev
        return self.switches

    def listRemotes(self):
        if len(self.remotes) == 0:
            for i in range(self.getNumberOfDevices()):
                devId = self.getDeviceId(i)
                model = self.getModel(devId)
                if 'switch' not in model and 'dimmer' not in model:
                    dev = {}
                    dev["id"] = devId
                    dev["name"] = self.getName(devId)
                    dev["model"] = model

                    self.remotes[devId] = dev
        return self.remotes
