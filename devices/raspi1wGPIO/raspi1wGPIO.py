#! /usr/bin/env python

#
# ago raspberry pi 1-wire GPIO device
#
# I am developing this driver on occidentalis distro from adfruit.com
# 
#
# /etc/opt/agocontrol/config.ini
#
# [raspi1wGPIO]
# interval=600 # maximum time(seconds) between reports
# change=0.2   # temperature change between reports
#

import agoclient
import threading
import time
import os
import sys
import syslog

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

client = agoclient.AgoConnection("raspi1wGPIO")

readInterval = agoclient.getConfigOption("raspi1wGPIO", "interval", "600")
interval = int(readInterval)

change = float(agoclient.getConfigOption("raspi1wGPIO", "change", "0.2"))




try:
    readDevices = (line.rstrip('\n') for line in open('/sys/bus/w1/devices/w1_bus_master1/w1_master_slaves'))
except IOError:
    syslog.syslog(syslog.LOG_ERR, 'No devices exiting')
    sys.exit()
    
devices = []
sensordata = {}

for device in readDevices:
    if 'not found.' in device:
        syslog.syslog(syslog.LOG_ERR, 'No devices exiting')
        sys.exit()
    devices.append(device)
    sensordata[(device, 'temp')] = 0
    sensordata[(device, 'lastreporttime')] = time.time()
    #print 'addDevice', device
    client.addDevice(device, "temperaturesensor")

print devices



class read1WGPIO(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
        while (True):
            for device in devices: 
                crcok = False
                errorcounter=0
                while (not crcok and (errorcounter < 4)):
                    #print 'errorcounter:', errorcounter
                    try:
                        slaveFile = open("/sys/bus/w1/devices/" + device + "/w1_slave") 
                        tempText = slaveFile.read() 
                        slaveFile.close() 
                    except IOError: 
                        syslog.syslog(syslog.LOG_ERR, "Error can\'t open device file", device)
                        errorcounter += 1
                    #print tempText
                    firstline = tempText.split("\n")[0]
                    crcstatus = firstline.split(" ")[11]
                    #print 'crcstatus:', crcstatus
                    if crcstatus == 'NO':
                        syslog.syslog(syslog.LOG_ERR, 'Bad CRC' )
                        errorcounter += 1
                    if crcstatus == 'YES':
                        secondline = tempText.split("\n")[1] 
                        temperaturedata = secondline.split(" ")[9] 
                        temperature = float(temperaturedata[2:]) 
                        temperature = temperature / 1000
                        #print device, temperature
                        if abs(sensordata[(device, 'temp')] - temperature) > change:
                            #print 'level change:', sensordata[(device, 'temp')]
                            client.emitEvent(device, "event.environment.temperaturechanged", temperature, "degC") 
                            sensordata[(device, 'temp')] = temperature
                            sensordata[(device, 'lastreporttime')] = time.time()
                        if time.time() > sensordata[(device, 'lastreporttime')] + interval:
                            #print 'interval:', sensordata[(device, 'temp')]
                            client.emitEvent(device, "event.environment.temperaturechanged", temperature, "degC") 
                            sensordata[(device, 'temp')] = temperature
                            sensordata[(device, 'lastreporttime')] = time.time()
                        crcok = True
            time.sleep(3)
            
      
background = read1WGPIO()
background.setDaemon(True)
background.start()

client.run()

