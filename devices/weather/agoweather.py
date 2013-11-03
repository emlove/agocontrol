#! /usr/bin/env python
#
# ago Weather device
# Copyright (c) 2013 by rages
#
# Create /etc/opt/agocontrol/conf.d/weather.conf
# [weather]
# locations_ID=ITLM2916
# tempunits = f
# waittime = 30
#
import agoclient
import time
import threading
import pywapi
import string


readID = agoclient.getConfigOption("weather","locations_ID","00000")
readTempUnits = agoclient.getConfigOption("weather","tempunits","f")
readWaitTime = int(agoclient.getConfigOption("weather","waittime","30"))
rain = "rain"
ex_temp = "ex_temp"
ex_umidity = "ex_umidity"

client = agoclient.AgoConnection("Weather")

client.addDevice(rain, "binarysensor")
client.addDevice(ex_temp, "temperaturesensor")
client.addDevice(ex_umidity, "multilevelsensor")

class testEvent(threading.Thread):
        def __init__(self,):
                threading.Thread.__init__(self)
        def run(self):
                while (True):
                        weather_com_result = pywapi.get_weather_from_weather_com(readID)
                        condizioni = weather_com_result['current_conditions']['text']
                        temperatura = float(weather_com_result['current_conditions']['temperature'])
                        umidita = float(weather_com_result['current_conditions']['humidity'])
                        if (readTempUnits == 'f' or readTempUnits == 'F'):
                                tempF = 9.0/5.0 * temperatura + 32
                                client.emitEvent(ex_temp, "event.environment.temperaturechanged", tempF, "degF")
                        else:
                                client.emitEvent(ex_temp, "event.environment.temperaturechanged", temperatura, "degC")
                        client.emitEvent(ex_umidity, "event.environment.humiditychanged", umidita, "%")
                        search_Rain = string.find(condizioni, "Rain")
                        search_Drizzle = string.find(condizioni, "Drizzle")
                        if (search_Rain >= 0) or (search_Drizzle >=0):
                                client.emitEvent(rain,"event.device.statechanged", "255", "")

                        else :
                                client.emitEvent(rain,"event.device.statechanged", "0", "")
                        time.sleep (readWaitTime)

background = testEvent()
background.setDaemon(True)
background.start()

client.run()

