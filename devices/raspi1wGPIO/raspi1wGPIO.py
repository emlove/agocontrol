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
# interval=600
#

import agoclient
import threading
import time
import os
import sys

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

client = agoclient.AgoConnection("raspi1wGPIO")

readInterval = agoclient.getConfigOption("raspi1wGPIO", "interval", "600")
interval = int(readInterval)


try:
    readDevices = (line.rstrip('\n') for line in open('/sys/bus/w1/devices/w1_bus_master1/w1_master_slaves'))
except IOError:
    print 'readDevices No devices exiting'
    sys.exit()
    
devices = []

for device in readDevices:
    if 'not found.' in device:
        print 'for device in readDevices: No devices exiting'
        sys.exit()
    devices.append(device)
    print 'addDevice', device
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
                    print 'errorcounter', errorcounter
                    try:
                        slaveFile = open("/sys/bus/w1/devices/" + device + "/w1_slave") 
                    except IOError: 
                        print "Error can\'t open device file", device
                        errorcounter += 1
                    tempText = slaveFile.read() 
                    slaveFile.close() 
                    print tempText
                    firstline = tempText.split("\n")[0]
                    crcstatus = firstline.split(" ")[11]
                    print crcstatus
                    if crcstatus == 'NO':
                        print 'Bad CRC' 
                        errorcounter += 1
                        time.sleep(3)
                    if crcstatus == 'YES':
                        secondline = tempText.split("\n")[1] 
                        temperaturedata = secondline.split(" ")[9] 
                        temperature = float(temperaturedata[2:]) 
                        temperature = temperature / 1000
                        client.emitEvent(device, "event.environment.temperaturechanged", temperature, "degC") 
                        print device, temperature
                        crcok = True
            print '---', interval, '---'
            time.sleep(interval)
            
      
background = read1WGPIO()
background.setDaemon(True)
background.start()

client.run()

