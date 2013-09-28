#!/usr/bin/python

import dbus
import json

print "Content-type: text/plain\n"

bus = dbus.SystemBus()

proxy = bus.get_object("org.freedesktop.systemd1",
                       "/org/freedesktop/systemd1")

iface = dbus.Interface(proxy, "org.freedesktop.systemd1.Manager")

def getState(unit):
    unit_obj = bus.get_object("org.freedesktop.systemd1", unit)
    props = dbus.Interface(unit_obj, "org.freedesktop.DBus.Properties")
    return props.Get("org.freedesktop.systemd1.Unit", "ActiveState")

units = ["agodatalogger.service", "agoevent.service", "agoresolver.service", "agorpc.service", "agoscenario.service", "agotimer.service"]

result = []

for unit in units:
    tmp = {}
    tmp["name"] = unit
    tmp["state"] = getState(iface.GetUnit(unit))
    result.append(tmp)
    

print json.dumps(result)
