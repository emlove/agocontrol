#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>

#include <syslog.h>

#include <cstdlib>
#include <iostream>

#include <sstream>
#include <algorithm>

#include "agoclient.h"

#ifndef SECURITYMAPFILE
#define SECURITYMAPFILE CONFIG_BASE_DIR "/maps/securitymap.json"
#endif


using namespace qpid::messaging;
using namespace qpid::types;
using namespace agocontrol;

AgoConnection *agoConnection;
std::string agocontroller;
qpid::types::Variant::Map securitymap;

void *alarmthread(void *param) {
	int delay = *((int *)param);
	Variant::Map content;
	cout << "Alarm triggered, delay: " << delay << endl;
	while (delay-- > 0) {
		cout << "count down: " << delay << endl;
		sleep(1);
	}
	agoConnection->sendMessage("event.security.intruderalert", content);
}

bool findList(qpid::types::Variant::List list, std::string elem) {
	qpid::types::Variant::List::const_iterator it = std::find(list.begin(), list.end(), elem);
	if (it == list.end()) return false;
	return true;
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	cout << "handling command: " << content << endl;
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "securitycontroller") {
		if (content["command"] == "sethousemode") {
			if (content["mode"].asString() != "") {
				securitymap["housemode"] = content["mode"].asString();
				cout << "setting mode: " << content["mode"] << endl;
				agoConnection->setGlobalVariable("housemode", content["mode"]);
				if (variantMapToJSONFile(securitymap, SECURITYMAPFILE)) {
					returnval["result"] = 0;
				} else {
					returnval["result"] = -1;
				}
			} else {
				returnval["result"] = -1;
			}

		} else if (content["command"] == "triggerzone") {
			std::string zone = content["zone"];
			qpid::types::Variant::Map zonemap;
			std::string housemode = securitymap["housemode"];
			if (!(securitymap["zones"].isVoid())) zonemap = securitymap["zones"].asMap();
			if (!(zonemap[housemode].isVoid())) {
				if (zonemap[housemode].getType() == qpid::types::VAR_LIST) {
					if (findList(zonemap[housemode].asList(), zone)) {
						static pthread_t securityThread;
						int delay = 30;
						pthread_create(&securityThread,NULL,alarmthread,(void *)&delay);
					}
				}	

			}
			returnval["result"] = 0;
		} else if (content["command"] == "setzones") {
			try {
				cout << "setzones request" << endl;
				qpid::types::Variant::Map newzones = content["zonemap"].asMap();
				cout << "zone content:" << newzones << endl;
				securitymap["zones"] = newzones;
				if (variantMapToJSONFile(securitymap, SECURITYMAPFILE)) {
					returnval["result"] = 0;
				} else {
					returnval["result"] = -1;
				}
			} catch (qpid::types::InvalidConversion) {
                                returnval["result"] = -1;
                        } catch (...) {
                                returnval["result"] = -1;
				returnval["error"] = "exception";
			}
		} else {
			returnval["result"] = -1;
		}
		
	} else {
		returnval["result"] = -1;
	}
	return returnval;
}

void eventHandler(std::string subject, qpid::types::Variant::Map content) {
	// string uuid = content["uuid"].asString();
	cout << subject << " " << content << endl;
}

int main(int argc, char** argv) {
	openlog(NULL, LOG_PID & LOG_CONS, LOG_DAEMON);
	agoConnection = new AgoConnection("security");

	securitymap = jsonFileToVariantMap(SECURITYMAPFILE);

	cout << "securitymap: " << securitymap << endl;
	std::string housemode = securitymap["housemode"];
	cout << "house mode: " << housemode;
	agoConnection->setGlobalVariable("housemode", housemode);
/*
	qpid::types::Variant::List armedZones;
	armedZones.push_back("hull");
	zonemap["armed"] = armedZones;

	securitymap["zones"] = zonemap;
	variantMapToJSONFile(securitymap, SECURITYMAPFILE);
*/
	agoConnection->addDevice("securitycontroller", "securitycontroller");
	agoConnection->addHandler(commandHandler);
	agoConnection->addEventHandler(eventHandler);

	int pin=atoi(getConfigOption("security", "pin", "1234").c_str());

	agoConnection->run();	

}


