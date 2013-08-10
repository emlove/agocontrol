# ago control - Ubiquiti Networks mFi mPower device
#
# copyright (c) 2013 Christoph Jaeger <office@diakonesis.at>
#
# Licensed under latest GNU GPL: http://www.gnu.org/licenses/gpl.html
# Thanks to Marek 'ConSi' Wajdzik who lead me to the correct path and his AirOS library!

# -*- coding: utf-8 -*-

class Device:
    "Simple class for managing mFi mPower devices wich are developed by Ubiquiti Networks"
    def __init__(self, address, username, password, port=80, protocol="http"):
        self.port = port
        self.username = username
        self.address = address
        self.protocol = protocol
        try:
            import datetime
            self.datetime = datetime
        except:
            raise self.Errors.datetimeImportError
        try:
            import json
            self.json = json
        except ImportError:
            raise self.Errors.jsonImportError
        try:
            import mechanize
        except ImportError:
            raise self.Errors.MechanizeImportError
        self.Connection = mechanize.Browser()
        try:
            self.Connection.open("%s://%s:%s/login.cgi" % (protocol, address, port))
        except:
            raise self.Errors.UBNTConnectionError
        self.Connection.select_form(nr=0)
        self.Connection["username"] = username
        self.Connection["password"] = password
        self.Connection.submit()

    def GetInfo(self):
        "Get various information about the device"
        return self.json.loads(self.Connection.open("%s://%s:%s/status.cgi" % (self.protocol, self.address, self.port)).read())

    def GetDevices(self):
        "Get various information about the power devices"
        return self.json.loads(self.Connection.open("%s://%s:%s/mfi/io.cgi?func=powerList&port=-1" % (self.protocol, self.address, self.port)).read())

    def SetDevice(self, id, value):
        "switch relais" 
        return self.Connection.open("%s://%s:%s/mfi/io.cgi?func=relayWrite&port=%s&value=%s" % (self.protocol, self.address, self.port, id, value)).read()

    def GetHostname(self):
        "Returns the device hostname"
        return self.GetInfo()["host"]["hostname"]

    def mPowerOSVersion(self):
        "Get mPower OS Version"
        return self.GetInfo()["host"]["fwversion"]

    class Errors:
        "PyUBNT Error Class"
        class SetRawOptionError(Exception):
                def __str__(self):
                    return "Error while changing raw config value"
        class UBNTConnectionError(Exception):
                def __str__(self):
                    return "Error while connectiong to Ubiquiti mFi mPower Device"
        class datetimeImportError(Exception):
                def __str__(self):
                    return "Error while importing datetime library"
        class jsonImportError(Exception):
                def __str__(self):
                    return "Error while importing json library"
        class MechanizeImportError(Exception):
                def __str__(self):
                    return "Error while importing mechanize (python-mechanize) library"
        class UBNTLoginError(Exception):
                def __str__(self):
                    return "Error while logging into device, probably you are using wrong username or password"
