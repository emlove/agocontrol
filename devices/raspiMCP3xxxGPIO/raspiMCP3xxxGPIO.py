#! /usr/bin/env python
#
#
# Copyright (C) 2012 Andreas Pagander
#
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#    
# See the GNU General Public License for more details.
#
#
# ago raspberry pi MCP3002 GPIO device
#
# I am developing this driver on occidentalis distro from adfruit.com
#
# /etc/opt/agocontrol/config.ini
#
# [raspiMCP300xGPIO]
#
# SPIMOSI = 10
# SPIMISO = 9
# SPICLK = 11
# SPICS = 8
# voltage_divider = 1
# inputs = 0
# interval=600
# change=0.1
#


import agoclient
import threading
import time
import subprocess
import re
import string
from time import gmtime, strftime
import RPi.GPIO as GPIO

client = agoclient.AgoConnection("raspiMCP3xxxGPIO")

SPIMOSI = int(agoclient.getConfigOption("raspiMCP3xxxGPIO", "SPIMOSI", "10"))
SPIMISO = int(agoclient.getConfigOption("raspiMCP3xxxGPIO", "SPIMISO", "9"))
SPICLK = int(agoclient.getConfigOption("raspiMCP3xxxGPIO", "SPICLK", "11"))
SPICS = int(agoclient.getConfigOption("raspiMCP3xxxGPIO", "SPICS", "8"))
vDiv = float(agoclient.getConfigOption("raspiMCP3xxxGPIO", "voltage_divider", "1"))
readInputs = agoclient.getConfigOption("raspiMCP3xxxGPIO", "inputs", "0,1")
interval = int(agoclient.getConfigOption("raspiMCP3xxxGPIO", "interval", "60"))
change = float(agoclient.getConfigOption("raspiMCP3xxxGPIO", "change", "0.1"))

inputs = map(int, readInputs.split(','))

deviceconfig = {}

for adcCh in inputs:
    deviceconfig[(adcCh, 'value')] = 0 
    deviceconfig[(adcCh, 'lastreporttime')] = time.time()
    client.addDevice(adcCh, "energysensor")
    
def readadc(adcCh, clockpin, mosipin, misopin, cspin):
    if ((adcCh > 1) or (adcCh < 0)):
        return -1
    if (adcCh == 0):
        commandout = 0x6
    else:
        commandout = 0x7
    GPIO.output(cspin, True)
    GPIO.output(clockpin, False) 
    GPIO.output(cspin, False)    
    commandout <<= 5    
    for i in range(3):
        if (commandout & 0x80):
            GPIO.output(mosipin, True)
        else:   
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
    adcout = 0
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if (GPIO.input(misopin)):
            adcout |= 0x1
    GPIO.output(cspin, True)
    adcout /= 2  
    return adcout

GPIO.setmode(GPIO.BCM)
GPIO.setup(SPIMOSI, GPIO.OUT)      
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
   
class readMCP300xGPIO(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
        while True:
            for adcCh in inputs:
                #print 'adcCh', adcCh
                adctot = 0
                for i in range(5):
                    read_adc = readadc(adcCh, SPICLK, SPIMOSI, SPIMISO, SPICS)
                    #print 'read_adc', read_adc
                    adctot += read_adc
                    time.sleep(0.05)
                read_adc = adctot / 5 / 1.0
                #print read_adc
                volts = round(read_adc*(3.33 / 1024.0)*vDiv, 2)
                #print "Battery Voltage:", adcCh, volts
                if abs(deviceconfig[(adcCh, 'value')] - volts) > change:
                    #print 'level change:', deviceconfig[(adcCh, 'value')]
                    client.emitEvent(adcCh , "event.environment.energychanged", volts, "V") 
                    deviceconfig[(adcCh, 'value')] = volts
                    deviceconfig[(adcCh, 'lastreporttime')] = time.time()
                if time.time() > deviceconfig[(adcCh, 'lastreporttime')] + interval:
                    #print 'interval:', deviceconfig[(adcCh, 'value')]
                    client.emitEvent(adcCh , "event.environment.energychanged", volts, "V") 
                    deviceconfig[(adcCh, 'temp')] = volts
                    deviceconfig[(adcCh, 'lastreporttime')] = time.time()
            time.sleep(3)
      
background = readMCP300xGPIO()
background.setDaemon(True)
background.start()

client.run()
