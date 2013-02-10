/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>

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

std::string commandHandler(qpid::types::Variant::Map content) {
	int valve = 0;
	valve = atoi(content["internalid"].asString().c_str());
	if (content["command"] == "on" ) {
		if (rain8.zoneOn(1,valve) != 0) {
			printf("can't switch on\n");
			return "unknown";
		} else {
			printf("switched on\n");
			return "255";
		}
	} else if (content["command"] == "off") {
		if (rain8.zoneOff(1,valve) != 0) {
			printf("can't switch off\n");
			return "unknown";
		} else {
			printf("switched off\n");
			return "0";
		}
	}
	return "";
}

int main(int argc, char **argv) {
	std::string devicefile;


	// szDevice = ExistingDF.GetString("device", "rain8net");
		devicefile="/dev/ttyS_01";

	if (rain8.init(devicefile.c_str()) != 0) {
		printf("can't open rainnet device %s\n", devicefile.c_str());
		exit(1);
	}
	if ((rc = rain8.comCheck()) != 0) {
		printf("can't talk to rainnet device %s, comcheck failed: %i\n", devicefile.c_str(),rc);
		exit(1);
	}
	printf("connection to rain8net established\n");

	AgoConnection agoConnection = AgoConnection();		
	printf("connection established\n");
	agoConnection.addDevice("123", "dimmer");
	agoConnection.addDevice("124", "switch");
	agoConnection.addHandler(commandHandler);

	unsigned char status;
	if (rain8.getStatus(1,status) == 0) {
		printf("can't get zone status, aborting\n");
		exit(1);
	} else {
		printf("Zone status: 8:%d 7:%d 6:%d 5:%d 4:%d 3:%d 2:%d 1:%d", (status & 128)?1:0, (status & 64)?1:0, (status &32)?1:0,(status&16)?1:0,(status&8)?1:0,(status&4)?1:0,(status&2)?1:0,(status&1)?1:0);
	}

	agoConnection.run();

}

