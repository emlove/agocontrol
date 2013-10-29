#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#include "agoclient.h"

#ifndef SCENARIOMAPFILE
#define SCENARIOMAPFILE CONFDIR "/maps/scenariomap.json"
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
		cout << sseq.str() << ": " << scenario[sseq.str()] << endl;
		if (element["command"] == "scenariosleep") {
			try {
				int delay = element["delay"];
				sleep(delay);
			} catch (qpid::types::InvalidConversion) {
				cout << "ERROR! Invalid conversion of delay value" << endl;
			}
			// cout << "scenariosleep special command detected. Delay:" << delay << endl;
		} else { 
			agoConnection->sendMessage(element);
		}
	}

	return NULL;
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "scenariocontroller") {
		if (content["command"] == "setscenario") {
			try {
				cout << "setscenario request" << endl;
				qpid::types::Variant::Map newscenario = content["scenariomap"].asMap();
				cout << "scnario content:" << newscenario << endl;
				std::string scenariouuid = content["scenario"].asString();
				if (scenariouuid == "") scenariouuid = generateUuid();
				cout << "scenario uuid:" << scenariouuid << endl;
				scenariomap[scenariouuid] = newscenario;
				agoConnection->addDevice(scenariouuid.c_str(), "scenario", true);
				if (variantMapToJSONFile(scenariomap, SCENARIOMAPFILE)) {
					returnval["result"] = 0;
					returnval["scenario"] = scenariouuid;
				} else {
					returnval["result"] = -1;
				}
			} catch (qpid::types::InvalidConversion) {
                                returnval["result"] = -1;
                        } catch (...) {
                                returnval["result"] = -1;
				returnval["error"] = "exception";
			}
		} else if (content["command"] == "getscenario") {
			try {
				std::string scenario = content["scenario"].asString();
				cout << "getscenario request:" << scenario << endl;
				returnval["result"] = 0;
				returnval["scenariomap"] = scenariomap[scenario].asMap();
				returnval["scenario"] = scenario;
			} catch (qpid::types::InvalidConversion) {
				returnval["result"] = -1;
			}
                } else if (content["command"] == "delscenario") {
			std::string scenario = content["scenario"].asString();
			cout << "delscenario request:" << scenario << endl;
			returnval["result"] = -1;
			if (scenario != "") {
				qpid::types::Variant::Map::iterator it = scenariomap.find(scenario);
				if (it != scenariomap.end()) {
					cout << "removing ago device" << scenario << endl;
					agoConnection->removeDevice(it->first.c_str());
					scenariomap.erase(it);
					if (variantMapToJSONFile(scenariomap, SCENARIOMAPFILE)) {
						returnval["result"] = 0;
					}
				}
			}
                } 

	} else {

		if ((content["command"] == "on") || (content["command"] == "run")) {
			cout << "spawning thread for scenario: " << internalid << endl;
			// runscenario((void *)&scenario);
			pthread_t execThread;
			pthread_create(&execThread, NULL, runscenario, (void *)&scenariomap[internalid].asMap());
			returnval["result"] = 0;
		} 

	}
	return returnval;
}

int main(int argc, char **argv) {
	agoConnection = new AgoConnection("scenario");	
	agoConnection->addDevice("scenariocontroller", "scenariocontroller");
	agoConnection->addHandler(commandHandler);

	scenariomap = jsonFileToVariantMap(SCENARIOMAPFILE);
	// cout  << scenariomap;
	for (qpid::types::Variant::Map::const_iterator it = scenariomap.begin(); it!=scenariomap.end(); it++) {
		cout << "adding scenario:" << it->first << ":" << it->second << endl;	
		agoConnection->addDevice(it->first.c_str(), "scenario", true);
	}
	agoConnection->run();
}
