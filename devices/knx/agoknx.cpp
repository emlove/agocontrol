/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

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

#include <tinyxml2.h>

#include <eibclient.h>
#include "Telegram.h"

#include "agoclient.h"

using namespace qpid::messaging;
using namespace qpid::types;
using namespace tinyxml2;
using namespace std;
using namespace agocontrol;

int polldelay = 0;

Variant::Map deviceMap;

EIBConnection *eibcon;
pthread_mutex_t mutexCon;
pthread_t listenerThread;

AgoConnection *agoConnection;

/**
 * parses the device XML file and creates a qpid::types::Variant::Map with the data
 */
bool loadDevices(string filename, Variant::Map& _deviceMap) {
	XMLDocument devicesFile;
	int returncode;

	printf("trying to open device file: %s\n", filename.c_str());
	returncode = devicesFile.LoadFile(filename.c_str());
	if (returncode != XML_NO_ERROR) {
		printf("error loading XML file, code: %i\n", returncode);
		return false;
	}

	printf("parsing file\n");
	XMLHandle docHandle(&devicesFile);
	XMLElement* device = docHandle.FirstChildElement( "devices" ).FirstChild().ToElement();
	if (device) {
		XMLElement *nextdevice = device;
		while (nextdevice != NULL) {
			Variant::Map content;

			printf("node: %s - ",nextdevice->Attribute("uuid"));
			printf("type: %s\n",nextdevice->Attribute("type"));

			content["devicetype"] = nextdevice->Attribute("type");
			XMLElement *ga = nextdevice->FirstChildElement( "ga" );
			if (ga) {
				XMLElement *nextga = ga;
				while (nextga != NULL) {
					printf("GA: %s - ",nextga->GetText());
					printf("type: %s\n",nextga->Attribute("type"));

					content[nextga->Attribute("type")]=nextga->GetText();
					nextga = nextga->NextSiblingElement();
				}
			}
			_deviceMap[nextdevice->Attribute("uuid")] = content;
			nextdevice = nextdevice->NextSiblingElement();
		}
	}
	return true;
}

/**
 * announces our devices in the devicemap to the resolver
 */
void reportDevices(Variant::Map devicemap) {
	for (Variant::Map::const_iterator it = devicemap.begin(); it != devicemap.end(); ++it) {
		Variant::Map device;
		Variant::Map content;
		Message event;

		// printf("uuid: %s\n", it->first.c_str());
		device = it->second.asMap();
		// printf("devicetype: %s\n", device["devicetype"].asString().c_str());
		agoConnection->addDevice(it->first.c_str(), device["devicetype"].asString().c_str(), true);
	}
}

/**
 * looks up the uuid for a specific GA - this is needed to match incoming telegrams to the right device
 */
string uuidFromGA(Variant::Map devicemap, string ga) {
	for (Variant::Map::const_iterator it = devicemap.begin(); it != devicemap.end(); ++it) {
		Variant::Map device;

		device = it->second.asMap();
		for (Variant::Map::const_iterator itd = device.begin(); itd != device.end(); itd++) {
			if (itd->second.asString() == ga) {
				// printf("GA %s belongs to %s\n", itd->second.asString().c_str(), it->first.c_str());
				return(it->first);
			}
		}
	}	
	return("");
}

/**
 * looks up the type for a specific GA - this is needed to match incoming telegrams to the right event type
 */
string typeFromGA(Variant::Map device, string ga) {
	for (Variant::Map::const_iterator itd = device.begin(); itd != device.end(); itd++) {
		if (itd->second.asString() == ga) {
			// printf("GA %s belongs to %s\n", itd->second.asString().c_str(), itd->first.c_str());
			return(itd->first);
		}
	}
	return("");
}
/**
 * thread to poll the knx bus for incoming telegrams
 */
void *listener(void *param) {
	int received = 0;

	printf("starting listener thread\n");
	while(true) {
		string uuid;
		pthread_mutex_lock (&mutexCon);
		received=EIB_Poll_Complete(eibcon);
		pthread_mutex_unlock (&mutexCon);
		switch(received) {
			case(-1): 
				printf("ERROR polling bus\n");
				exit(-1);
				break;
				;;
			case(0)	:
				usleep(polldelay);
				break;
				;;
			default:
				Telegram tl;
				pthread_mutex_lock (&mutexCon);
				tl.receivefrom(eibcon);
				pthread_mutex_unlock (&mutexCon);
				printf("received Telegram from: %s; to: %s; type: %s shortdata %d\n",
									Telegram::paddrtostring(tl.getSrcAddress()).c_str(),
									Telegram::gaddrtostring(tl.getGroupAddress()).c_str(),
									tl.decodeType().c_str(),
									tl.getShortUserData());
				uuid = uuidFromGA(deviceMap, Telegram::gaddrtostring(tl.getGroupAddress()));
				if (uuid != "") {
					string type = typeFromGA(deviceMap[uuid].asMap(),Telegram::gaddrtostring(tl.getGroupAddress()));
					if (type != "") {
						printf("handling telegram, GA from telegram belongs to: %s - type: %s\n",uuid.c_str(),type.c_str());
						if(type == "onoff" || type == "onoffstatus") { 
							agoConnection->emitEvent(uuid.c_str(), "event.device.statechanged", tl.getShortUserData()==1 ? 255 : 0, "");
						} else if (type == "setlevel" || type == "levelstatus") {
							int data = tl.getUIntData(); 
							agoConnection->emitEvent(uuid.c_str(), "event.device.statechanged", data, "");
						} else if (type == "temperature") {
							agoConnection->emitEvent(uuid.c_str(), "event.environment.temperaturechanged", tl.getFloatData(), "degC");
						} else if (type == "brightness") {
							agoConnection->emitEvent(uuid.c_str(), "event.environment.brightnesschanged", tl.getFloatData(), "lux");
						} else if (type == "energy") {
							agoConnection->emitEvent(uuid.c_str(), "event.environment.energychanged", tl.getFloatData(), "mA");
						} else if (type == "energyusage") {
							unsigned char buffer[4];
							if (tl.getUserData(buffer,4) == 4) {
								printf("USER DATA: %x %x %x %x \n", buffer[0],buffer[1],buffer[2],buffer[3]);
							}
							// event.setSubject("event.environment.powerchanged");
						} else if (type == "binary") {
							agoConnection->emitEvent(uuid.c_str(), "event.security.sensortriggered", tl.getShortUserData()==1 ? 255 : 0, "");
						}
					}
				}
				break;
				;;
		}
	}

	return NULL;
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	printf("received command  %s for device %s\n", content["command"].asString().c_str(), internalid.c_str());
	qpid::types::Variant::Map::const_iterator it = deviceMap.find(internalid);
	qpid::types::Variant::Map device;
	if (it != deviceMap.end()) {
		device=it->second.asMap();
	} else {
		returnval["result"]=-1;
	}
	Telegram *tg = new Telegram();
	eibaddr_t dest;
	bool handled=true;
	if (content["command"] == "on") {
		string destGA = device["onoff"];
		dest = Telegram::stringtogaddr(destGA);
		if (device["devicetype"]=="drapes") {
			tg->setShortUserData(0);
		} else {
			tg->setShortUserData(1);
		}
	} else if (content["command"] == "off") {
		string destGA = device["onoff"];
		dest = Telegram::stringtogaddr(destGA);
		if (device["devicetype"]=="drapes") {
			tg->setShortUserData(1);
		} else {
			tg->setShortUserData(0);
		}
	} else if (content["command"] == "stop") {
		string destGA = device["stop"];
		dest = Telegram::stringtogaddr(destGA);
		tg->setShortUserData(1);
	} else if (content["command"] == "push") {
		string destGA = device["push"];
		dest = Telegram::stringtogaddr(destGA);
		tg->setShortUserData(0);
	} else if (content["command"] == "setlevel") {
		int level=0;
		string destGA = device["setlevel"];
		dest = Telegram::stringtogaddr(destGA);
		level = atoi(content["level"].asString().c_str());
		tg->setDataFromChar(level);
	} else if (content["command"] == "setcolor") {
		int level=0;
		Telegram *tg2 = new Telegram();
		Telegram *tg3 = new Telegram();
		tg->setDataFromChar(atoi(content["red"].asString().c_str()));
		tg->setGroupAddress(Telegram::stringtogaddr(device["red"].asString()));
		tg2->setDataFromChar(atoi(content["green"].asString().c_str()));
		tg2->setGroupAddress(Telegram::stringtogaddr(device["green"].asString()));
		tg3->setDataFromChar(atoi(content["blue"].asString().c_str()));
		tg3->setGroupAddress(Telegram::stringtogaddr(device["blue"].asString()));
		pthread_mutex_lock (&mutexCon);
		printf("sending telegram\n");
		tg2->sendTo(eibcon);
		printf("sending telegram\n");
		tg3->sendTo(eibcon);
		pthread_mutex_unlock (&mutexCon);

	} else {
		handled=false;
	}
	if (handled) {	
		tg->setGroupAddress(dest);
		printf("sending telegram\n");
		pthread_mutex_lock (&mutexCon);
		bool result = tg->sendTo(eibcon);
		pthread_mutex_unlock (&mutexCon);
		printf("Result: %i\n",result);
		returnval["result"]=result ? 0 : -1;
	} else {
		printf("ERROR, received undhandled command\n");
		returnval["result"]=-1;
	}
	return returnval;
}

int main(int argc, char **argv) {
	std::string eibdurl;
	std::string devicesFile;

	// parse config
	eibdurl=getConfigOption("knx", "url", "ip:127.0.0.1");
	polldelay=atoi(getConfigOption("knx", "polldelay", "5000").c_str());
	devicesFile=getConfigOption("knx", "devicesfile", "/etc/opt/agocontrol/knx/devices.xml");

	// load xml file into map
	if (!loadDevices(devicesFile, deviceMap)) {
		printf("ERROR, can't load device xml\n");
		exit(-1);
	}

	printf("connecting to eibd\n");
	eibcon = EIBSocketURL(eibdurl.c_str());
	if (!eibcon) {
		printf("can't connect to url %s\n",eibdurl.c_str());
		exit(-1);
	}

	if (EIBOpen_GroupSocket (eibcon, 0) == -1)
	{
		EIBClose(eibcon);
		printf("can't open EIB Group Socket\n");
		exit(-1);
	}

	// connect to broker
	agoConnection = new AgoConnection("knx");

	// announce devices to resolver
	reportDevices(deviceMap);

	pthread_mutex_init(&mutexCon,NULL);
	pthread_create(&listenerThread, NULL, listener, NULL);

	agoConnection->addHandler(commandHandler);
	agoConnection->run();
}

