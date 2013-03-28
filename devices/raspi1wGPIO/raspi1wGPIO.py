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

client = agoclient.AgoConnection("raspi1wGPIO")

readInterval = agoclient.getConfigOption("raspi1wGPIO", "interval", "600")
interval = int(readInterval)

readDevices = (line.rstrip('\n') for line in open('/sys/bus/w1/devices/w1_bus_master1/w1_master_slaves'))

devices = []

for device in readDevices:
    devices.append(device)
    client.addDevice(device, "multilevelsensor")

print devices



class read1WGPIO(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
        while (True):
            for device in devices:        
                slaveFile = open("/sys/bus/w1/devices/" + device + "/w1_slave") 
                tempText = slaveFile.read() 
                slaveFile.close() 
                secondline = tempText.split("\n")[1] 
                temperaturedata = secondline.split(" ")[9] 
                temperature = float(temperaturedata[2:]) 
                temperature = temperature / 1000
                client.emitEvent(device, "event.environment.temperaturechanged", temperature, "C") 
                print device, temperature
            print '---', interval, '---'
            time.sleep(interval)
            
      
background = read1WGPIO()
background.setDaemon(True)
background.start()

client.run()

