#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

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

void *runscenario(void * _scenario) {
	qpid::types::Variant::Map *scenariop = (qpid::types::Variant::Map *) _scenario;
	qpid::types::Variant::Map scenario = *scenariop;
	// build sorted list of scenario elements
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
		if (scenario["command"] == "scenariosleep") {
			int delay = scenario["delay"];
			sleep(delay);
		} else { 
			agoConnection->sendMessage(element);
		}
	}

	return NULL;
}

std::string commandHandler(qpid::types::Variant::Map content) {
	std::string internalid = content["internalid"].asString();
	if (internalid == "scenariocontroller") {
		if (content["command"] == "setscenario") {


		} else if (content["command"] == "getscenario") {


                } else if (content["command"] == "delscenario") {


                } 

	} else {

		if (content["command"] == "on" ) {
			cout << "spawning thread for scenario: " << internalid << endl;
			// runscenario((void *)&scenario);
			pthread_t execThread;
			pthread_create(&execThread, NULL, runscenario, (void *)&scenariomap[internalid].asMap());
		} 

	}
	return "";
}

int main(int argc, char **argv) {
	agoConnection = new AgoConnection("agoscenario");	
	agoConnection->addDevice("scenariocontroller", "scenariocontroller");
	agoConnection->addHandler(commandHandler);

	scenariomap = jsonFileToVariantMap(SCENARIOMAP);
	// cout  << scenariomap;
	for (qpid::types::Variant::Map::const_iterator it = scenariomap.begin(); it!=scenariomap.end(); it++) {
		cout << "adding scenario:" << it->first << ":" << it->second << endl;	
		agoConnection->addDevice(it->first.c_str(), "scenario", true);
	}
	agoConnection->run();
}
