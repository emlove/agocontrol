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
#define SECURITYMAPFILE CONFDIR "/maps/securitymap.json"
#endif

using namespace qpid::messaging;
using namespace qpid::types;
using namespace agocontrol;

AgoConnection *agoConnection;
std::string agocontroller;
static pthread_t securityThread;
bool isSecurityThreadRunning = false;
qpid::types::Variant::Map securitymap;

// example map: {"housemode":"armed","zones":{"armed":[{"zone":"hull","delay":12}]}}
bool checkPin(std::string _pin) {
	stringstream pins(getConfigOption("security", "pin", "0815"));
	string pin;
	while (getline(pins, pin, ',')) {
		if (_pin == pin) return true;
	}
	return false;
}


bool findList(qpid::types::Variant::List list, std::string elem) {
	//qpid::types::Variant::List::const_iterator it = std::find(list.begin(), list.end(), elem);
	for (qpid::types::Variant::List::const_iterator it = list.begin(); it != list.end(); it++) {
		if (it->getType() == qpid::types::VAR_MAP) {
			qpid::types::Variant::Map map = it->asMap();
			if (map["zone"].asString() == elem) {
				// cout << "found zone: " << map["zone"] << endl;
				return true;
			}
		}

	}
	return false;
}

int getZoneDelay(qpid::types::Variant::Map smap, std::string elem) {
	qpid::types::Variant::Map zonemap;
	qpid::types::Variant::List list;
	std::string housemode = securitymap["housemode"];
	if (!(smap["zones"].isVoid())) zonemap = smap["zones"].asMap();
	if (!(zonemap[housemode].isVoid())) {
		if (zonemap[housemode].getType() == qpid::types::VAR_LIST) {
			list = zonemap[housemode].asList();
			for (qpid::types::Variant::List::const_iterator it = list.begin(); it != list.end(); it++) {
				if (it->getType() == qpid::types::VAR_MAP) {
					qpid::types::Variant::Map map = it->asMap();
					if (map["zone"].asString() == elem) {
						// cout << "found zone: " << map["zone"] << endl;
						if (map["delay"].isVoid()) {
							return 0;
						} else {
							int delay = map["delay"].asUint8();
							return delay;
						}
					}
				}

			}
		}
	}
	return 0;
}

void *alarmthread(void *param) {
	std::string zone;
	if (param) zone = (const char*)param;
	int delay=getZoneDelay(securitymap, zone);	
	Variant::Map content;
	content["zone"]=zone;
	cout << "Alarm triggered, zone: " << zone << " delay: " << delay << endl;
	while (delay-- > 0) {
		Variant::Map countdowneventcontent;
		countdowneventcontent["delay"]=delay;
		countdowneventcontent["zone"]=zone;
		agoConnection->emitEvent("securitycontroller", "event.security.countdown", countdowneventcontent);
		cout << "count down: " << delay << endl;
		sleep(1);
	}
	cout << "sending alarm event" << endl;
	agoConnection->emitEvent("securitycontroller", "event.security.intruderalert", content);
	isSecurityThreadRunning = false;
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	cout << "handling command: " << content << endl;
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "securitycontroller") {
		if (content["command"] == "sethousemode") {
			// TODO: handle delay
			if (content["mode"].asString() != "") {
				if (checkPin(content["pin"].asString())) {
					securitymap["housemode"] = content["mode"].asString();
					cout << "setting mode: " << content["mode"] << endl;
					agoConnection->setGlobalVariable("housemode", content["mode"]);
					Variant::Map eventcontent;
					eventcontent["housemode"]= content["mode"].asString();
					agoConnection->emitEvent("securitycontroller", "event.security.housemodechanged", eventcontent);

					if (variantMapToJSONFile(securitymap, SECURITYMAPFILE)) {
						returnval["result"] = 0;
					} else {
						returnval["result"] = -1;
					}
				} else {
					cout << "ERROR: invalid pin" << endl;
					returnval["result"] = -1;
					returnval["error"] = "invalid pin";
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
					// let's see if the zone is active in the current house mode
					if (findList(zonemap[housemode].asList(), zone)) {
						const char *_zone = zone.c_str();
						// check if there is already an alarmthread running
						if (isSecurityThreadRunning  == false) {
							if (pthread_create(&securityThread,NULL,alarmthread,(void *)_zone) != 0) {
								cout << "ERROR: can't start alarmthread!" << endl;
								returnval["result"] = -1;
							} else {
								isSecurityThreadRunning = true;
								returnval["result"] = 0;
							}
						} else {
							cout << "alarmthread already running" << endl;
							returnval["result"] = 0;
						}
					}
				}	

			}
		} else if (content["command"] == "setzones") {
			// TODO: this might need some kind of protection
			try {
				cout << "setzones request" << endl;
				qpid::types::Variant::Map newzones = content["zonemap"].asMap();
				cout << "zone content:" << newzones << endl;
				securitymap["zones"] = newzones;
				if (variantMapToJSONFile(securitymap, SECURITYMAPFILE)) {
					returnval["result"] = 0;
				} else {
					returnval["result"] = -1;
					returnval["error"]="cannot save securitymap";
				}
			} catch (qpid::types::InvalidConversion) {
                                returnval["result"] = -1;
				returnval["error"] = "invalid conversion";
                        } catch (...) {
                                returnval["result"] = -1;
				returnval["error"] = "exception";
			}
		} else if (content["command"] == "getzones") {
			if (!(securitymap["zones"].isVoid())) {
				returnval["zonemap"] == securitymap["zones"].asMap();
				returnval["result"]=0;
			} else {
				returnval["result"] = -1;
				returnval["error"] = "empty map";
			}

		} else if (content["command"] == "cancel") {
			if (checkPin(content["pin"].asString())) {
				if (isSecurityThreadRunning) {
					if (pthread_cancel(securityThread) != 0) {
						cout << "ERROR: cannot cancel alarm thread!" << endl;
						returnval["result"] = -1;
						returnval["error"] = "cancel failed";
					} else {
						isSecurityThreadRunning = false;
						returnval["result"] = 0;
						cout << "alarm cancelled" << endl;
					}

				} else {
					cout << "ERROR: no alarm thread running" << endl;
					returnval["result"] = -1;
					returnval["error"] = "no alarm thread";
				}
			} else {
				cout << "ERROR: invalid pin" << endl;
				returnval["result"] = -1;
				returnval["error"] = "invalid pin";
			}
		} else {
			returnval["result"] = -1;
			returnval["error"] = "unknown command";
		}
		
	} else {
		returnval["result"] = -1;
		returnval["error"] = "unknown device";
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
//	agoConnection->addEventHandler(eventHandler);

	agoConnection->run();	

}


