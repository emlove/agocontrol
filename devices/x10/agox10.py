import agoclient
import threading
import time
import logging
from x10.controllers.cm11 import CM11

dev = CM11('/dev/ttyUSB1')
dev.open()

#  Dictionaries to decrypt hex values sent from CM11A to house/device codes as well as function on/off
#  Other functions exist but on/off are the only ones handled.  All other functions are ignored
#  Functions are displayed as decimal values ON = 255 and OFF = 0
#  See http://www.smarthome.com/manuals/protocol.txt for details

x10_house =  {'6': 'A', 'e': 'B', '2': 'C', 'a': 'D', '1': 'E', '9': 'F', '5': 'G', 'd': 'H', '7': 'I', 'f': 'J', '3': 'K', 'b': 'L', '0': 'M', '8': 'N', '4': 'O', 'c': 'P'}
x10_device = {'6': '1', 'e': '2', '2': '3', 'a': '4', '1': '5', '9': '6', '5': '7', 'd': '8', '7': '9', 'f': '10', '3': '11', 'b': '12', '0': '13', '8': '14', '4': '15', 'c': '16'}
x10_funct  = {'2': '255', '3': '0'}


client = agoclient.AgoConnection("X10")

# This section handles sending X10 devices over the CM11A using Python-X10

# this class will be instantiated and spawned into background to not block the messageHandler
class x10send(threading.Thread):
    def __init__(self, id, functioncommand):
        threading.Thread.__init__(self)
        self.id = id
        self.functioncommand = functioncommand
    def run(self):
        if self.functioncommand == "on":
                print "switching on: " + self.id
                dev.actuator(self.id).on()
                client.emitEvent(self.id, "event.device.statechanged", "255", "")
        if self.functioncommand == "off":
                print "switching off: " + self.id
                dev.actuator(self.id).off()
                client.emitEvent(self.id, "event.device.statechanged", "0", "")

def messageHandler(internalid, content):
        if "command" in content:
		# spawn into background
		background = x10send(internalid, content["command"])
		background.setDaemon(True)
		background.start()

# specify our message handler method
client.addHandler(messageHandler)

# X10 device configuration
client.addDevice("A2", "switch")
client.addDevice("A3", "switch")
client.addDevice("A9", "switch")
client.addDevice("B3", "switch")
client.addDevice("B4", "switch")
client.addDevice("B5", "switch")
client.addDevice("B9", "switch")
client.addDevice("B12", "switch")

# This section is used to monitor for incoming RF signals on the CM11A


class testEvent(threading.Thread):
    def __init__(self,):
        threading.Thread.__init__(self)
    def run(self):
                loop=1
                while (loop == 1):
                        data=dev.read()
                        # Check to see if the CM11A received a command
                        if (data == 90):
                                # Send 0xc3 to CM11A to tell it to send the data
                                dev.write(0xc3)

                                # Read the data.  This should be modified as this code only reads
                                # The first four bytes

                                # The first byte send tells how many bytes to expect
                                first=dev.read()
                                first="%x"%(first)

                                # Second tells how many total address and functions to expect
                                second=dev.read()
                                second="%x"%(second)

                                # This should probably read in some sort of array but for now this is device address (ie B2
                                third=dev.read()
                                third= "%x"%(third)
                                # This is another value.  For now this is the function (ie ON)
                                fourth=dev.read()
                                fourth = "%x"%(fourth)

                                # Print values (debug)
                                print x10_house[third [:1]] + x10_device[third [1:]] + " " + x10_funct[fourth [1:]];

                                # Look up values in dicitionaries and assign variables
                                send_x10_address = x10_house[third [:1]] + x10_device[third [1:]];
                                send_x10_command = x10_funct[fourth [1:]];

                                # Use these values to change device states in Ago Control
                                print "here they are: " + send_x10_address + send_x10_command;
                                if (send_x10_command == 0) or (send_x10_command == 255):
                                        client.emitEvent(send_x10_address , "event.device.statechanged", send_x10_command , "");

background = testEvent()
background.setDaemon(True)
background.start()

client.run()
