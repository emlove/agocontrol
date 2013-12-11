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
	int rid = 0; rid = atol(internalid.c_str());
	if (content["command"] == "on") {
		myESP3->fourbsCentralCommandDimLevel(rid,0x64,1);
	} else if (content["command"] == "off") {
		myESP3->fourbsCentralCommandDimOff(rid);
	} else if (content["command"] == "setlevel") {
		uint8_t level = 0;
		level = content["level"];
		myESP3->fourbsCentralCommandDimLevel(rid,level,1);
	}
	returnval["result"] = 0;
	return returnval;
}

int main(int argc, char **argv) {
	std::string devicefile;
	devicefile=getConfigOption("enocean3", "device", "/dev/ttyAMA0");
	myESP3 = new esp3::ESP3(devicefile);
	myESP3->init();

	AgoConnection _agoConnection = AgoConnection("enocean3");
	agoConnection = &_agoConnection;

	printf("connection to agocontrol established\n");

	agoConnection->addHandler(commandHandler);

	stringstream dimmers(getConfigOption("enocean3", "dimmers", "1"));
	string dimmer;
	while (getline(dimmers, dimmer, ',')) {
		agoConnection->addDevice(dimmer.c_str(), "dimmer");
		cout << "adding rid " << dimmer << " as dimmer" << endl;
	} 

	agoConnection->run();	
}
