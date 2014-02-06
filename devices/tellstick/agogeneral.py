############################################
#
# General ago functions
#
############################################

import logging
import syslog

import sqlite3




# Check if a device exists in the inventory

def deviceExist(deviceUUID):
    conn = sqlite3.connect('/etc/opt/agocontrol/db/inventory.db')
    found = False
    cursor = conn.execute("SELECT name from devices where uuid='" + deviceUUID + "'")
    for row in cursor:
        found = True
    conn.close()
    return found


# Only for test purposes

if __name__ == '__main__':
    a = deviceExist("fdc3a35d-2e22-4ff3-afad-eb004f8a6dbc")
    print ("a=" + a)


