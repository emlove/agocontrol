/*
     Copyright (C) 2009 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>
#include <sstream>
#include <uuid/uuid.h>
#include <stdlib.h>

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>

#include "agoclient.h"
#include "esp3.h"


using namespace std;
using namespace agocontrol;

esp3::ESP3 *myESP3;

AgoConnection *agoConnection;

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "enoceancontroller") {
		if (content["command"] == "teachframe") {
			int channel = content["channel"];
			std::string profile = content["profile"];
			if (profile == "central command dimming") {
				myESP3->fourbsCentralCommandDimTeachin(channel);
			} else {
				myESP3->fourbsCentralCommandSwitchTeachin(channel);
			}
			returnval["result"] = 0;
		} else if (content["command"] == "setlearnmode") {
			returnval["result"] = -1;
		} else if (content["command"] == "setidbase") {
			returnval["result"] = -1;
		}
	} else {
		int rid = 0; rid = atol(internalid.c_str());
		if (content["command"] == "on") {
			if (agoConnection->getDeviceType(internalid.c_str())=="dimmer") {
				myESP3->fourbsCentralCommandDimLevel(rid,0x64,1);
			} else {
				myESP3->fourbsCentralCommandSwitchOn(rid);
			}
		} else if (content["command"] == "off") {
			if (agoConnection->getDeviceType(internalid.c_str())=="dimmer") {
				myESP3->fourbsCentralCommandDimOff(rid);
			} else {
				myESP3->fourbsCentralCommandSwitchOff(rid);
			}
		} else if (content["command"] == "setlevel") {
			uint8_t level = 0;
			level = content["level"];
			myESP3->fourbsCentralCommandDimLevel(rid,level,1);
		}
		returnval["result"] = 0;
	}
	return returnval;
}

int main(int argc, char **argv) {
	std::string devicefile;
	devicefile=getConfigOption("enocean3", "device", "/dev/ttyAMA0");
	myESP3 = new esp3::ESP3(devicefile);
	if (!myESP3->init()) {
		cerr << "ERROR, cannot initalize enocean ESP3 protocol on device " << devicefile << endl;
		exit(-1);
	}

	AgoConnection _agoConnection = AgoConnection("enocean3");
	agoConnection = &_agoConnection;

	printf("connection to agocontrol established\n");

	agoConnection->addHandler(commandHandler);
	agoConnection->addDevice("enoceancontroller", "enoceancontroller");

	stringstream dimmers(getConfigOption("enocean3", "dimmers", "1"));
	string dimmer;
	while (getline(dimmers, dimmer, ',')) {
		agoConnection->addDevice(dimmer.c_str(), "dimmer");
		cout << "adding rid " << dimmer << " as dimmer" << endl;
	} 
	stringstream switches(getConfigOption("enocean3", "switches", "20"));
	string switchdevice;
	while (getline(switches, switchdevice, ',')) {
		agoConnection->addDevice(switchdevice.c_str(), "switch");
		cout << "adding rid " << switchdevice << " as switch" << endl;
	} 

	agoConnection->run();	
}
