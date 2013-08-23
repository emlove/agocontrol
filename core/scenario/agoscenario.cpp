#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#include "agoclient.h"

#ifndef SCENARIOMAP
#define SCENARIOMAP "/etc/opt/agocontrol/scenariomap.json"
#endif

using namespace std;
using namespace agocontrol;

qpid::types::Variant::Map scenariomap;
AgoConnection *agoConnection;

bool compare(int a, int b) {
	return a < b ? false : true;
}

std::string commandHandler(qpid::types::Variant::Map content) {
	std::string internalid = content["internalid"].asString();
	if (internalid == "scenariocontroller") {


	} else {

		if (content["command"] == "on" ) {
			cout << "executing scenario: " << internalid << endl;
			// build sorted list of scenario elements
			qpid::types::Variant::Map scenario = scenariomap[internalid].asMap();
			std::list<int> elements;
			for (qpid::types::Variant::Map::const_iterator it = scenario.begin(); it!= scenario.end(); it++) {
				// cout << it->first << endl;
				// cout << it->second << endl;
				elements.push_back(atoi(it->first.c_str()));
			}
			// cout << "elements: " << elements << endl;
			elements.sort();
			for (std::list<int>::const_iterator it = elements.begin(); it != elements.end(); it++) {
				// cout << *it << endl;
				int seq = *it;
				stringstream sseq;
				sseq << seq;
				qpid::types::Variant::Map element = scenario[sseq.str()].asMap();
				cout << sseq.str() << ":" << scenario[sseq.str()] << endl;
				if (content["command"] == "scenariosleep") {
					int delay = content["delay"];
					sleep(delay);
				} else { 
					agoConnection->sendMessage(element);
				}
			}
		} 

	}
	return "";
}

int main(int argc, char **argv) {
	agoConnection = new AgoConnection("agoscenario");	
	agoConnection->addDevice("scenariocontroller", "scenariocontroller");
	agoConnection->addHandler(commandHandler);

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
	// cout  << scenariomap;
	for (qpid::types::Variant::Map::const_iterator it = scenariomap.begin(); it!=scenariomap.end(); it++) {
		cout << "adding scenario:" << it->first << ":" << it->second << endl;	
		agoConnection->addDevice(it->first.c_str(), "scenario", true);
	}
	agoConnection->run();
}
