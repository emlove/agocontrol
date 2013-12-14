#!/usr/bin/python

import json
import psutil
from os.path import basename

print "Content-type: text/plain\n"

def getState(unit):
    unit_obj = bus.get_object("org.freedesktop.systemd1", unit)
    props = dbus.Interface(unit_obj, "org.freedesktop.DBus.Properties")
    return props.Get("org.freedesktop.systemd1.Unit", "ActiveState")

result = []
error = False

try:
    #try systemd first using dbus
    bus = dbus.SystemBus()
    proxy = bus.get_object("org.freedesktop.systemd1","/org/freedesktop/systemd1")
    iface = dbus.Interface(proxy, "org.freedesktop.systemd1.Manager")
    units = ["agodatalogger.service", "agoevent.service", "agoresolver.service", "agorpc.service", "agoscenario.service", "agotimer.service"]
    for unit in units:
        tmp = {}
        tmp["name"] = unit
        tmp["state"] = getState(iface.GetUnit(unit))
        result.append(tmp)
except:
    #maybe systemd does not exist on this system
    error = True

if error:
    try:
        #try more generic way to detect running processes
        units = {"agodatalogger":False, "agoevent":False, "agoresolver":False, "agorpc":False, "agoscenario":False, "agotimer":False}

        #search for all 'ago...' services
        for proc in psutil.get_process_list():
            if proc.name.startswith('ago'):
                tmp = {}
                tmp['name'] = proc.name
                tmp['state'] = proc.is_running()
                result.append(tmp)
                if units.has_key(proc.name):
                    units[proc.name] = True
            elif 'python' in proc.name and 'ago' in proc.cmdline[1]:
                tmp = {}
                tmp['name'] = basename(proc.cmdline[1])
                tmp['state'] = proc.is_running()
                result.append(tmp)

        #search for missing mandatory processes
        for unit in units.keys():
            if not units[unit]:
                tmp = {}
                tmp['name'] = unit
                tmp['state'] = False
                result.append(tmp)
    except:
        #failed to get running processes using process list
        pass

print json.dumps(result)
