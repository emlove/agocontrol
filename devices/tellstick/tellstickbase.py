#!/usr/bin/python
AGO_TELLSTICK_VERSION = '0.0.9'
############################################
#
# Tellstick base class
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
import syslog as syslog

class tellstickbase:
    """Base class used for Tellstick, Tellstick Duo and Tellstck Net devices"""
    def __init__(self):
        self.TELLSTICK_TURNON = 1  # check values
        self.TELLSTICK_TURNOFF = 2
        self.TELLSTICK_DIM = 4

        self.TELLSTICK_TEMPERATURE = 1 #td.TELLSTICK_TEMPERATURE
        self.TELLSTICK_HUMIDITY = 2 #td.TELLSTICK_HUMIDITY
        self.sensors={}
        self.switches={}
        self.remotes={}

    def __get__(self, obj, objtype=None):
        pass

    def __set__(self, obj, val):
        pass

    def __delete__(self, obj):
        pass

    def init(self, SensorPollDelay, TempUnits):
        pass
    def close(self):
        pass
    def turnOn(self, devId):
        pass
    def turnOff(self, devId):
        pass
    def getErrorString(self, resCode):
        pass
    def dim(self, level):
        pass
    def getName(self,devId):
        pass
    def methodsReadable(self, method):
        pass
    def getNumberOfDevices(self):
        pass
    def listSensors(self):
        pass
    def listSwitches(self):
        pass
    def listRemotes(self):
        pass
    def getDeviceId(self,i):
        pass
    def getModel(self, devId):
        pass
    def registerDeviceEvent(self, deviceEvent):
        pass
    def registerDeviceChangedEvent(self, deviceEvent):
        pass
    def registerSensorEvent(self, deviceEvent):
        pass
