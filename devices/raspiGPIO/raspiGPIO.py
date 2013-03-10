import RPi.GPIO as GPIO
import xml.etree.ElementTree as ET
import time
import sys
import syslog
import ConfigParser
import optparse
import Queue
import threading

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN


config = ConfigParser.ConfigParser()
config.read('/etc/opt/agocontrol/config.ini')

try:
    username = config.get("system","username")
except ConfigParser.NoOptionError, e:
    username = "agocontrol"

try:
    password = config.get("system","password")
except ConfigParser.NoOptionError, e:
    password = "letmein"

try:
    broker = config.get("system","broker")
except ConfigParser.NoOptionError, e:
    broker = "localhost"

try:
    debug = config.get("system","debug")
except ConfigParser.NoOptionError, e:
    debug = "WARN"

if debug=="DEBUG":
    enable("qpid", DEBUG)
else:
    enable("qpid", WARN)

 
parser = optparse.OptionParser(usage="usage: %prog <command> [options] [ PARAMETERS ... ]",
                               description="send automation control commands")
parser.add_option("-b", "--broker", default=broker, help="hostname of broker (default %default)")
parser.add_option("-u", "--username", default=username, help="specify a username")
parser.add_option("-P", "--password", default=password, help="specify a password")

opts, args = parser.parse_args()

connection = Connection(opts.broker, username=opts.username, password=opts.password,  reconnect=True)
connection.open()
session = connection.session()
receiver = session.receiver("agocontrol; {create: always, node: {type: topic}}")
sender = session.sender("agocontrol; {create: always, node: {type: topic}}")

def reportdevice(uuid='3e9b5bb8-58e9-11e2-8772-f23c91aec05e', type='sensor', product='GPIO device'):
    try:
        content = {}
        content["devicetype"]=type
        content["uuid"] = uuid
        content["product"] = product
        message = Message(content=content,subject="event.device.announce")
        sender.send(message)
    except SendError, e:
        print e
        
def sendSensorTriggerEvent(uuid, level):
        try:
                content = {}
                content["uuid"] = uuid
                content["level"] = level
                message = Message(content=content,subject="event.security.sensortriggered")
                sender.send(message)
        except SendError, e:
                print e

def sendStateChangedEvent(uuid, level):
        try:
                content = {}
                content["uuid"] = uuid
                content["level"] = level
                message = Message(content=content,subject="event.device.statechanged")
                sender.send(message)
        except SendError, e:
                print e

treeDevices = ET.parse('/etc/opt/agocontrol/raspiGPIO/devices.xml')
rootDevices = treeDevices.getroot()

devices = {}
for child in rootDevices:
    devices[child.get('uuid')] = {'type': child.get('type'), 'pin': int(child.get('pin'))}
#debug
print devices

def discovery():
    for (uuid) in devices:
        reportdevice(uuid=uuid, type=devices[uuid]['type'])

discovery()


GPIO.setmode(GPIO.BCM)
#GPIO.cleanup()

for uuid in devices:
    if devices[uuid]['type'] == 'switch':
        GPIO.setup(devices[uuid]['pin'], GPIO.OUT)
    if devices[uuid]['type'] == 'binarysensor':
        GPIO.setup(devices[uuid]['pin'], GPIO.IN)

inputQueue = Queue.Queue()

class readGPIO(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)    
    def run(self):
        prev_input = {}
        input = {}
        for uuid in devices:
                if devices[uuid]['type'] == 'binarysensor':
                    prev_input[devices[uuid]['pin']] = 0
                    input[devices[uuid]['pin']] = 0
        counter = 0
        while True:
            for uuid in devices:
                if devices[uuid]['type'] == 'binarysensor':
                  input[devices[uuid]['pin']] = GPIO.input(devices[uuid]['pin'])
                  # if the last reading was low and this one high
                  if (not prev_input[devices[uuid]['pin']]) and input[devices[uuid]['pin']]:
                    print"Button pressed -- pin:", devices[uuid]['pin'], "uuid:" , uuid
                    inputQueue.put([uuid, 1])
                  if prev_input[devices[uuid]['pin']] and (not input[devices[uuid]['pin']]):
                    print"Button pressed -- pin:", devices[uuid]['pin'], "uuid:" , uuid
                    inputQueue.put([uuid, 0])
                  prev_input[devices[uuid]['pin']] = input[devices[uuid]['pin']]
            time.sleep(0.05)
      
background = readGPIO()
background.setDaemon(True)
background.start()

while True:
  while not inputQueue.empty():
        item = inputQueue.get()
        print "while not inputQueue.empty(): uuid:", item[0], "value:" , item[1]
        sendSensorTriggerEvent(item[0], item[1])
  try:
      message = receiver.fetch(timeout=1)
      if message.content:
                if 'command' in message.content:
                    print message
                    if message.content['command'] == 'discover':
                        syslog.syslog(syslog.LOG_NOTICE, "discovering devices")
                        discovery()
                    elif message.content['command'] == 'inventory':
                        syslog.syslog(syslog.LOG_NOTICE, "ignoring inventory command")
                    else:
                        if 'uuid' in message.content:
                            for (uuid) in devices:
                                if message.content['uuid'] == uuid:
                                    command = ''
                                    if message.content['command'] == 'on':
                                        sendStateChangedEvent(uuid, 255)
                                        GPIO.output(devices[uuid]['pin'], True)
                                        print "device switched on"
                                    if message.content['command'] == 'off':
                                        sendStateChangedEvent(uuid, 0)
                                        GPIO.output(devices[uuid]['pin'], False)
                                        print "device switched off"
                                    # send reply
                                    if message.reply_to:
                                        replysender = session.sender(message.reply_to)
                                        response = Message("ACK")
                                        try:
                                            replysender.send(response)
                                        except SendError, e:
                                            print "Can't send ACK: ", e
                                            
  except Empty, e:
        pass
  except KeyError, e:
        print "key error in command evaluation", e
  except ReceiverError, e:
        print "ReceiverError", e
        time.sleep(1)