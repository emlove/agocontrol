/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>
#include <sstream>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#include <termios.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#include "agoclient.h"

#include "rain8.h"
rain8net rain8;
int rc;

using namespace std;
using namespace agocontrol;

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	int valve = 0;
	valve = atoi(content["internalid"].asString().c_str());
	printf("command: %s internal id: %i\n", content["command"].asString().c_str(), valve);
	if (content["command"] == "on" ) {
		if (rain8.zoneOn(1,valve) != 0) {
			printf("can't switch on\n");
			returnval["result"] = -1;
		} else {
			printf("switched on\n");
			returnval["result"] = 0;
		}
	} else if (content["command"] == "off") {
		if (rain8.zoneOff(1,valve) != 0) {
			printf("can't switch off\n");
			returnval["result"] = -1;
		} else {
			printf("switched off\n");
			returnval["result"] = 0;
		}
	}
	return returnval;
}

int main(int argc, char **argv) {
	std::string devicefile;

	devicefile=getConfigOption("rain8net", "device", "/dev/ttyS_01");

	if (rain8.init(devicefile.c_str()) != 0) {
		printf("can't open rainnet device %s\n", devicefile.c_str());
		exit(1);
	}
	rain8.setTimeout(10000);
	if ((rc = rain8.comCheck()) != 0) {
		printf("can't talk to rainnet device %s, comcheck failed: %i\n", devicefile.c_str(),rc);
		exit(1);
	}
	printf("connection to rain8net established\n");

	AgoConnection agoConnection = AgoConnection("rain8net");		
	printf("connection to agocontrol established\n");

	for (int i=1; i<9; i++) {
		std::stringstream valve;
		valve << i;
		agoConnection.addDevice(valve.str().c_str(), "switch");
	}
	agoConnection.addHandler(commandHandler);

	printf("fetching zone status\n");
	unsigned char status;
	if (rain8.getStatus(1,status) == 0) {
		printf("can't get zone status, aborting\n");
		exit(1);
	} else {
		printf("Zone status: 8:%d 7:%d 6:%d 5:%d 4:%d 3:%d 2:%d 1:%d\n", (status & 128)?1:0, (status & 64)?1:0, (status &32)?1:0,(status&16)?1:0,(status&8)?1:0,(status&4)?1:0,(status&2)?1:0,(status&1)?1:0);
	}
	printf("waiting for messages\n");
	agoConnection.run();

}

