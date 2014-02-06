#!/usr/bin/python
import json
import httplib, urllib
import requests

from datetime import date, datetime

def sendTemperaturNu(temp):
        r = requests.get('http://www.temperatur.nu/rapportera.php?hash=' + reporthash + '&t=' + str(temp))
        status = r.status_code
        data = r.text

        if r.status_code == 200 and "ok! (" in data and len(data) > 6:
            return True
        else:
            print "something went wrong when reporting. response=" + data
            # Some logging needed here
            return False

def sendOpenWeatherMap(lat, lon, alt, user, password, temp = None, tempUnit = None, hum = None):
    parms = 'lat=' + lat + '&long=' + lon + '&alt=' + alt
    if temp is not None:
        if tempUnit == "degF":
            tempF = (float(temp)-32)*5/9
            parms += '&temp=' + str(tempF)
        else:
            parms += '&temp=' + str(temp)

    if hum is not None:
        parms += "&humidity=" + str(hum)

    print parms

    r = requests.get('http://openweathermap.org/data/post?' + parms, auth = (user, password))
    status = r.status_code
    print "status=" + str(status)
    data = r.text
    print "data=" + data

    if r.status_code == 200 and "ok! (" in data and len(data) > 6:
        return True
    else:
        print "something went wrong when reporting. response=" + data
        # Some logging needed here
        return False




# Parameter	 Unit	 Description
# ========== ======= =========================================
# wind_dir	 Degrees Wind direction
# wind_speed m/s	 Wind speed
# wind_gust	 m/s	 Speed of wind gust
# temp	     degC	     Temperature
# humidity	 RH %	 Relative humidity
# pressure		     Atmospheric pressure [Clarification needed]
# rain_1h	 mm	     Rain in the last hour
# rain_24h	 mm	     Rain in the last 24 hours
# rain_today mm	     Rain since midnight
# snow	     mm 	 Snow in the last 24 hours
# lum	     W/m2	 Brightness [Clarification needed]
# lat	     Decimal degrees	Latitude
# long	     Decimal degrees	Longitude
# alt	     m	     Altitude
# radiation		     Radiation [Clarification needed]
# dewpoint	 degC	     Dew point
# uv		         UV index
# name	     String	 Weather station name
def sendWeatherUnderground(stationid, password, temp, tempUnit):
    if tempUnit == "degC":
        tempstr = 'tempc'
        #tempF = float(temp)*9/5+32
    else:
        tempstr = 'tempf'
        #tempF = float(temp)

    data = {
        'ID': stationid,
        'PASSWORD': password,
        'dateutc': str(datetime.utcnow()),
        tempstr: str(temp),
        'action': 'updateraw',
        'softwaretype': 'ago control',
        'realtime': '1',
        'rtfreq': '2.5'
    }
    url = 'http://rtupdate.wunderground.com/weatherstation/updateweatherstation.php'

    r = requests.post(url=url, data=data)

    #Raise exception if status code is not 200
    r.raise_for_status()
    if r.text == 'success\n':
        return True
    else:
        print "something went wrong when reporting. response=" + r.text
        # Some logging needed here
        return False

lat = "56.045038"
long = "12.718345"
alt = "43.21"
stationId = 'ISKNECOU3'

#sendOpenWeatherMap(temp=2.1, user=''  password='Up5Wbr1HTzOrHN35kAXH')
#sendOpenWeatherMap(lat, long, alt, user = 'Joakim', password='Up5Wbr1HTzOrHN35kAXH', temp="1.4", tempUnit="degC")
#sendOpenWeatherMap(lat, long, alt, user = 'Joakim', password='Up5Wbr1HTzOrHN35kAXH',  hum="50")

sendWeatherUnderground(stationId, '5hTXjO31ktazN4DwSfhp', 1.3, "degC")
#WeatherUndergroupd 5hTXjO31ktazN4DwSfhp
# Key 71a97c99beb4b66e
# Station ISKNECOU3

