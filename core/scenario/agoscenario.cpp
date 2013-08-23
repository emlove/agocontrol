#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <string>
#include <iostream>
#include <cerrno>

#include "agoclient.h"

#ifndef SCENARIOMAP
#define SCENARIOMAP "/etc/opt/agocontrol/scenariomap.json"
#endif

using namespace std;
using namespace agocontrol;

qpid::types::Variant::Map scenariomap;

std::string commandHandler(qpid::types::Variant::Map content) {
	std::string internalid = content["internalid"].asString();
	if (internalid == "scenariocontroller") {


	} else {

		if (content["command"] == "on" ) {
			cout << "executing scenario: " << internalid << " -> " << scenariomap[internalid] << endl;
		} 

	}
	return "";
}

int main(int argc, char **argv) {
	AgoConnection agoConnection = AgoConnection("agoscenario");	
	agoConnection.addDevice("scenariocontroller", "scenariocontroller");
	agoConnection.addHandler(commandHandler);

	string content;
	ifstream mapfile (SCENARIOMAP);
	if (mapfile.is_open()) {
		while (mapfile.good()) {
			string line;
			getline(mapfile, line);
			content += line;
		}
		mapfile.close();
	}
	scenariomap = jsonStringToVariantMap(content);
	cout  << scenariomap;
	for (qpid::types::Variant::Map::const_iterator it = scenariomap.begin(); it!=scenariomap.end(); it++) {
		cout << "adding scenario:" << it->first << ":" << it->second << endl;	
		agoConnection.addDevice(it->first.c_str(), "scenario", true);
	}
	agoConnection.run();
}
