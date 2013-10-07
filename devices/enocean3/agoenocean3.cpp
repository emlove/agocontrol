/*
     Copyright (C) 2009 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>
#include <uuid/uuid.h>
#include <stdlib.h>

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>

#include "agoclient.h"
#include "esp3.h"

using namespace std;
using namespace agocontrol;

AgoConnection *agoConnection;

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	returnval["result"] = 0;
	return returnval;
}

int main(int argc, char **argv) {
	std::string devicefile;
	devicefile=getConfigOption("enocean3", "device", "/dev/ttyAMA0");

	AgoConnection _agoConnection = AgoConnection("enocean3");
	agoConnection = &_agoConnection;

	printf("connection to agocontrol established\n");

	agoConnection->addHandler(commandHandler);

	esp3::init(devicefile);
	while (true) esp3::readFrame();

	agoConnection->run();	
}
