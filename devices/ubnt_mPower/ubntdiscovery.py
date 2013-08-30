# ago control - Ubiquiti Networks device discovery tool
#
# Copyright (C) 2013 Christoph Jaeger <office@diakonesis.at>
#
# This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details.

# test on target: tcpdump -i eth0 port 10001 -XX
# send string to box: printf '\x01\x00\x00\x00' | nc -p 48000 -w1 -u 192.168.4.177 10001
from socket import *

def parsedata(data):
	result = {}
	ba = bytearray(data)
	size = ba[3]
	# print "size:", size
	x = 4;
	while (x != size -1):
		if (ba[x+1] == 0):
			if (ba[x] == 01):
				if (ba[x+2] == 6):
					mac = ""
					for y in range(x+3, x+3+6):
						mac += "%0.2x" % ba[y]
						if (y != x+3+6-1):
							mac += ":"
					result["mac"] = mac
			if (ba[x] == 0xb):
				hostname = ""
				for y in range(x+3, x+3+ba[x+2]):
					hostname += "%c" % ba[y]
				result["hostname"] = hostname
			if (ba[x] == 0xd):
				ssid = ""
				for y in range(x+3, x+3+ba[x+2]):
					ssid += "%c" % ba[y]
				result["ssid"] = ssid
			if (ba[x] == 0x3):
				fwver = ""
				for y in range(x+3, x+3+ba[x+2]):
					fwver += "%c" % ba[y]
				result["fw"] = fwver
			if (ba[x] == 0xc):
				devicetype = ""
				for y in range(x+3, x+3+ba[x+2]):
					devicetype += "%c" % ba[y]
				result["type"] = devicetype
		x+= 1
	return result

cs = socket(AF_INET, SOCK_DGRAM)
cs.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
cs.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
cs.settimeout(5)
cs.sendto('\x01\x00\x00\x00', ('255.255.255.255', 10001))

devices = {}

while True:
        try:
                global v
                v, addr = cs.recvfrom(1024)
                content = parsedata(v)
                if content["mac"] not in devices:
                        devices[content["mac"]] = {"ip": addr[0], "hostname": content["hostname"], "ssid": content["ssid"], "type": content["type"], "firmware": content["fw"]}
        except timeout:
                cs.close()
                break

if devices:
        print devices
else:
        print "No device found"
