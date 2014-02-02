#!/usr/bin/python
AGO_TELLSTICK_VERSION = '0.0.9'
############################################
#
# Tellstick Net class
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

from tellstickbase import tellstickbase
import sys, getopt, httplib, urllib, json, os, thread, time
import oauth.oauth as oauth
import datetime
from configobj import ConfigObj


class tellsticknet(tellstickbase):
    """Class used for Tellstick Net devices with direct access to Telldus Live API"""
    def __init__(self):
        debug = True
        self.config = ConfigObj("/etc/opt/agocontrol/conf.d/tellstick.conf")

        try:
            self.PUBLIC_KEY = self.config['keys']['PUBLIC_KEY']
        except KeyError:
            error ("PUBLIC_KEY missing in config file /etc/opt/agocontrol/conf.d/tellstick.conf Cannot continue.")
            quit()

        try:
            self.PRIVATE_KEY = self.config['keys']['PRIVATE_KEY']
        except KeyError:
            error ("PRIVATE_KEY missing in config file /etc/opt/agocontrol/conf.d/tellstick.conf Cannot continue.")
            quit()

        self.TELLSTICK_TURNON = 1
        self.TELLSTICK_TURNOFF = 2
        self.TELLSTICK_BELL = 4
        self.TELLSTICK_DIM = 16
        self.TELLSTICK_UP = 128
        self.TELLSTICK_DOWN = 256

        self.TELLSTICK_TEMPERATURE = 1 #td.TELLSTICK_TEMPERATURE
        self.TELLSTICK_HUMIDITY = 2 #td.TELLSTICK_HUMIDITY

        self.sensors={}
        self.switches={}
        self.remotes={}

        self.devices={}
        self.models={}
        self.names={}
        self.devicesRetrieved = False

        #super(tellsticknet, self).__init__() # call base class init method

    def __get__(self, obj, objtype=None):
        pass

    def __set__(self, obj, val):
        pass

    def __delete__(self, obj):
        pass

    def init(self, SensorPollDelay, TempUnits):
        self.SUPPORTED_METHODS = self.TELLSTICK_TURNON | self.TELLSTICK_TURNOFF | self.TELLSTICK_DIM
        self.consumer = oauth.OAuthConsumer(self.PUBLIC_KEY, self.PRIVATE_KEY)
        self.token = oauth.OAuthToken(self.config['telldus']['token'], self.config['telldus']['tokenSecret'])
        self.SensorPollDelay  = SensorPollDelay
        self.TempUnits = TempUnits

    def close(self):
        pass
        #return td.close()

    def turnOn(self, devId):
        return self.doMethod(devId, self.TELLSTICK_TURNON)

    def turnOff(self, devId):
        return self.doMethod(devId, self.TELLSTICK_TURNOFF)

    def getErrorString(self, resCode):
        return resCode #Telldus API returns strings, not resCodes. Just for making this compatible with Tellstick Duo API


    def dim(self, devId, level):
        return self.doMethod(devId, self.TELLSTICK_DIM, level)

    def getName(self,devId):
        try:
            return self.names[devId]
        except:
            response = self.doRequest('device/info', {'id': devId, 'supportedMethods': self.SUPPORTED_METHODS})

            if ('error' in response):
                name = ''
                retString = response['error']
                print ("retString=" + retString)
            else:
                name = response['name']
                self.names[devId] = response['name']

            return name

    def methodsReadable(self, method, default):
        #return td.methodsReadable (method, default)
        return "X"

    def getNumberOfDevices(self):
        if len(self.switches) > 0:
            return len(self.switches)
        else:
            self.listSwitches()
            return len(self.switches)

    def getDeviceId(self,i):
        return (self.devices[i])

    def getModel(self, devId):
        if devId in self.switches:
            s = self.switches[devId]
            return s["model"]
        elif devId in self.remotes:
            s = self.remotes[devId]
            return s["model"]
        elif devId in self.sensors:
            s = self.sensors[devId]
            return s["model"]

        response = self.doRequest('device/info', {'id': devId, 'supportedMethods': self.SUPPORTED_METHODS})

        if ('error' in response):
            model = ''
            retString = response['error']
            print ("retString=" + retString)
        else:
            if response['type'] == 'device':
                self.models[devId] = response['model']
            elif response['type'] == "group":
                self.models[devId] = 'group'
                # Devices in the group stored in  response['devices']

        return self.models[devId]
# dead code

    def registerDeviceEvent(self, deviceEvent):
        pass
        #return td.registerDeviceEvent(deviceEvent)
    def registerDeviceChangedEvent(self, deviceEvent):
        pass
        #return td.registerDeviceChangedEvent(deviceEvent)
    def registerSensorEvent(self, deviceEvent):
        thread.start_new_thread (self.sensorThread, (deviceEvent, 0))

    def doMethod(self, deviceId, methodId, methodValue = 0):
        response = self.doRequest('device/info', {'id': deviceId}) # Put this in local cache to avoid lookup over the net

        if (methodId == self.TELLSTICK_TURNON):
            method = 'on'
        elif (methodId == self.TELLSTICK_TURNOFF):
            method = 'off'
        # elif (methodId == self.TELLSTICK_BELL):
        #     method = 'bell'
        # elif (methodId == self.TELLSTICK_UP):
        #     method = 'up'
        # elif (methodId == self.TELLSTICK_DOWN):
        #     method = 'down'

        if ('error' in response):
            name = ''
            retString = response['error']
        else:
            name = response['name']
            response = self.doRequest('device/command', {'id': deviceId, 'method': methodId, 'value': methodValue})
            if ('error' in response):
                retString = response['error']
            else:
                retString = response['status']

        # if (methodId in (self.TELLSTICK_TURNON, self.TELLSTICK_TURNOFF)):
        #     print("Turning %s device %s, %s - %s" % ( method, deviceId, name, retString))
        # elif (methodId in (self.TELLSTICK_BELL, self.TELLSTICK_UP, self.TELLSTICK_DOWN)):
        #     print("Sending %s to: %s %s - %s" % (method, deviceId, name, retString))
        # elif (methodId == self.TELLSTICK_DIM):
        #     print("Dimming device: %s %s to %s - %s" % (deviceId, name, methodValue, retString))
        return retString

    def doRequest(self, method, params):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, token=self.token, http_method='GET', http_url="http://api.telldus.com/json/" + method, parameters=params)
        oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), self.consumer, self.token)
        headers = oauth_request.to_header()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

        conn = httplib.HTTPConnection("api.telldus.com:80")
        try:
            conn.request('GET', "/json/" + method + "?" + urllib.urlencode(params, True).replace('+', '%20'), headers=headers)

            response = conn.getresponse()
            return json.load(response)
        except:
            return json.loads('{"error": "Network connectivity issue"}')



    def requestToken(self):
        consumer = oauth.OAuthConsumer(self.PUBLIC_KEY, self.PRIVATE_KEY)
        request = oauth.OAuthRequest.from_consumer_and_token(consumer, http_url='http://api.telldus.com/oauth/requestToken')
        request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), consumer, None)
        conn = httplib.HTTPConnection('api.telldus.com:80')
        conn.request(request.http_method, '/oauth/requestToken', headers=request.to_header())

        resp = conn.getresponse().read()
        token = oauth.OAuthToken.from_string(resp)
        print 'Open the following url in your webbrowser:\nhttp://api.telldus.com/oauth/authorize?oauth_token=%s\n' % token.key
        print 'After logging in and accepting to use this application run:\n%s --authenticate' % (sys.argv[0])
        self.config['telldus']['requestToken'] = str(token.key)
        self.config['telldus']['requestTokenSecret'] = str(token.secret)
        self.saveConfig()

    def listSwitches(self):
        response = self.doRequest('devices/list', {'supportedMethods': self.SUPPORTED_METHODS})
        noDevices= len(response['device'])
        print("Number of devices: %i" % noDevices)
        i = 0
        for device in response['device']:
            devId = device["id"]
            model = self.getModel(devId)

            dev = {}
            dev["id"] = devId
            dev["name"] = device["name"]
            dev["model"] = model
            if 'switch'in model or 'dimmer' in model:
                if 'dimmer' in model:
                    dev["isDimmer"] = True
                else:
                    dev["isDimmer"] = False
                self.devices[i] = device["id"]
                i = i +1
                self.names[device["id"]] = device["name"]
                self.switches[devId] = dev
            elif 'group' not in model:
                self.remotes[devId] = dev
        self.devicesRetrieved = True

        return self.switches

    def listRemotes(self):
        if not self.devicesRetrieved:
            self.listSwitches()
        return self.remotes

    def listSensors(self):
        response = self.doRequest('sensors/list', {'includeIgnored': 1, 'includeValues': 1})
        print("Number of sensors: %i" % len(response['sensor']))
        for sensor in response['sensor']:
            if sensor["id"] not in self.sensors:
                s = {}
                #lastupdate = datetime.datetime.fromtimestamp(int(sensor['lastUpdated']))
                #print "%s\t%s\t%s" % (sensor['id'], sensor['name'], lastupdate)
                devId = str(sensor["id"])
                s["id"] = devId
                s["name"] = sensor["name"]
                s["new"] = True
                if "temp" in sensor:
                    s["isTempSensor"] = True
                    s["temp"] = float(sensor["temp"]) # C/ F
                    s["lastTemp"] = -274.0
                else:
                    s["isTempSensor"] = False

                if "humidity" in sensor:
                    s["id"] = devId
                    s["isHumiditySensor"] = True
                    s["humidity"] = float(sensor["humidity"])
                    s["lastHumidity"] = -999.0
                else:
                    s["isHumiditySensor"] = False

                if "temp" in sensor and "humidity" in sensor:
                    s["isMultiLevel"] = True
                else:
                    s["isMultiLevel"] = False

                self.sensors[devId] = s
                self.names[sensor["id"]] = devId

        return self.sensors

#    def getSensorData(self, sensorId):
#        response = self.doRequest('sensor/info', {'id': sensorId })
#        lastupdate = datetime.datetime.fromtimestamp(int(response['lastUpdated']))
#        sensor_name = response['name']
#        for data in response['data']:
#            print "%s\t%s\t%s\t%s" % (sensor_name, data['name'], data['value'], lastupdate)
#            #if data['name'] == "temp":

    def sensorThread (self, sensorCallback, dummy):

        while (True):
            for devId, dev in self.sensors.iteritems():
                response = self.doRequest('sensor/info', {'id': dev["id"] })
                lastupdate = datetime.datetime.fromtimestamp(int(response['lastUpdated']))

                for data in response['data']:
                    #print "%s\t%s\t%s\t%s" % (response['name'], data['name'], data['value'], lastupdate)

                    if data['name'] == 'temp' and float(data['value']) != self.sensors[devId]["lastTemp"]:
                        tempC = float(data['value'])
                        self.sensors[devId]["lastTemp"] = tempC
                        if tempC != self.sensors[devId]["temp"]:
                            self.sensors[devId]["temp"] = tempC
                            sensorCallback(protocol="", model="temp", devId=devId, dataType=0, value=tempC, timestamp=lastupdate, callbackId=None)

                    if data['name'] == 'humidity' and float(data['value']) != self.sensors[devId]["lastHumidity"]:
                        humidity = float(data['value'])
                        self.sensors[devId]["lastHumidity"] = humidity
                        if humidity<> self.sensors[devId]["humidity"]:
                            self.sensors[devId]["humidity"] = humidity
                            sensorCallback (protocol = "", model = "humidity", devId = devId, dataType = 0, value = humidity, timestamp = lastupdate, callbackId = None)

            time.sleep (float(self.SensorPollDelay))

























