#!/usr/bin/python
############################################
#
# Wake on LAN support for ago control
#
# Developed by  Joakim Lindbom
#               (Joakim.Lindbom@gmail.com)
#               2014-01-18
#
AGO_WOL_VERSION = '0.0.1'
#
############################################

import agoclient
import socket
import struct
import threading, time
import sys, syslog, logging
from configobj import ConfigObj
import pinger

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)

logging.basicConfig(filename='/var/log/wake_on_lan.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO) #level=logging.DEBUG
#logging.setLevel( logging.INFO )

def info (text):
    logging.info (text)
    syslog.syslog(syslog.LOG_INFO, text)
    if debug:
        print "INF " + text + "\n"
def debug (text):
    logging.debug (text)
    syslog.syslog(syslog.LOG_DEBUG, text)
    if debug:
        print "DBG " + text + "\n"
def error (text):
    logging.error(text)
    syslog.syslog(syslog.LOG_ERR, text)
    if debug:
        print "ERR " + text + "\n"
def warning(text):
    logging.warning (text)
    syslog.syslog(syslog.LOG_WARNING, text)
    if debug:
        print "WRN " + text + "\n"


def wake_on_lan(macaddress):
    """ Switches on remote computers using WOL. """

    # Check macaddress format and try to compensate.
    if len(macaddress) == 12:
        pass
    elif len(macaddress) == 12 + 5:
        sep = macaddress[2]
        macaddress = macaddress.replace(sep, '')
    else:
        raise ValueError('Incorrect MAC address format')

    # Pad the synchronization stream.
    data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
    send_data = ''

    # Split up the hex values and pack.
    for i in range(0, len(data), 2):
        send_data = ''.join([send_data,struct.pack('B', int(data[i: i + 2], 16))])

    # Broadcast it to the LAN.
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(send_data, ('<broadcast>', 7))

def messageHandler(internalid, content):
    if "command" in content:
        if content["command"] == "on":
            try:

                resCode = wake_on_lan(computers[internalid])
            except ValueError as e:
                error ("Cannot send WOL package to device=" + str(internalid) + " : " + str(e))
            else:
                client.emitEvent(internalid, "event.device.statechanged", "255", "")
                if debug:
                    info("Sending WOL package to device " + str(internalid) + " mac=" + computers[internalid])

def ping(host):
    response = pinger.echo(host)

    if response != None:
        if debug:
            info (host  + ' is up!')
        return True
    else:
        if debug:
            info (host + ' is down!')
        return False

class pingEvent(threading.Thread):
    def __init__(self, sleep):
        threading.Thread.__init__(self)
        self.sleep = sleep
    def run(self):
        while (True):
            for x in hosts:
                if debug:
                    info ("pinging x=" + hosts[x])
                if hosts[x] != '':
                    res = ping (hosts[x])
                    if res==True:
                        client.emitEvent(x, "event.device.statechanged", "255", "")
                    else:
                        client.emitEvent(x, "event.device.statechanged", "0", "")
            time.sleep (float(self.sleep))


info( "+------------------------------------------------------------")
info( "+ wake_on_lan.py startup. Version=" + AGO_WOL_VERSION)
info( "+------------------------------------------------------------")

debug=False
client = agoclient.AgoConnection("wake_on_lan")
if (agoclient.getConfigOption("wake_on_lan", "debug", "false").lower() == "true"):
    debug = True

config = ConfigObj("/etc/opt/agocontrol/conf.d/wake_on_lan.conf")

try:
    pingsleep = config['wake_on_lan']['polltime']
except:
    pingsleep = 300

section = config['Computers']
computers={}
hosts={}
for y in section:
    client.addDevice(config['Computers'][y]['name'], "computer")
    computers[config['Computers'][y]['name']] = config['Computers'][y]['mac']
    try:
        hosts[config['Computers'][y]['name']] = config['Computers'][y]['host']
    except:
        if debug:
            info ("No host for device=" + config['Computers'][y]['name'] + ". Will not report state for this device.")

client.addHandler(messageHandler)

background = pingEvent(pingsleep)
background.setDaemon(True)
background.start()

client.run()
