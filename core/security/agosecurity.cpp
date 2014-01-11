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

using namespace qpid::messaging;
using namespace qpid::types;
using namespace agocontrol;

AgoConnection *agoConnection;
std::string agocontroller;
std::string housemode;
qpid::types::Variant::Map zonemap;

void *security(void *param) {
	Variant::Map content;
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
				housemode = content["mode"].asString();
				cout << "setting mode: " << housemode << endl;
				agoConnection->setGlobalVariable("housemode", Variant(housemode));
				returnval["result"] = 0;
			} else {
				returnval["result"] = -1;
			}

		} else if (content["command"] == "triggerzone") {
			std::string zone = content["zone"];
			if (!(zonemap[housemode].isVoid())) {
				if (zonemap[housemode].getType() == qpid::types::VAR_LIST) {
					if (findList(zonemap[housemode].asList(), zone)) {

					}
				}	

			}
		} else if (content["command"] == "setzones") {
			returnval["result"] = 0;

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

	agoConnection->addDevice("securitycontroller", "securitycontroller");
	agoConnection->addHandler(commandHandler);
	agoConnection->addEventHandler(eventHandler);

	int pin=atoi(getConfigOption("security", "pin", "1234").c_str());

	static pthread_t securityThread;
	pthread_create(&securityThread,NULL,security,NULL);

	agoConnection->run();	

}


