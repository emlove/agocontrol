#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#include "agoclient.h"
#include "bool.h"

#ifndef EVENTMAPFILE
#define EVENTMAPFILE CONFDIR "/maps/eventmap.json"
#endif

using namespace std;
using namespace agocontrol;
using namespace qpid::types;

qpid::types::Variant::Map eventmap;
AgoConnection *agoConnection;

double variantToDouble(qpid::types::Variant v) {
	double result;
	switch(v.getType()) {
		case VAR_DOUBLE:
			result = v.asDouble();	
			break;
		case VAR_FLOAT:
			result = v.asFloat();	
			break;
		case VAR_BOOL:
			result = v.asBool();
			break;
		case VAR_STRING:
			result = atof(v.asString().c_str());
			break;
		case VAR_INT8:
			result = v.asInt8();
			break;
		case VAR_INT16:
			result = v.asInt16();
			break;
		case VAR_INT32:
			result = v.asInt32();
			break;
		case VAR_INT64:
			result = v.asInt64();
			break;
		case VAR_UINT8:
			result = v.asUint8();
			break;
		case VAR_UINT16:
			result = v.asUint16();
			break;
		case VAR_UINT32:
			result = v.asUint32();
			break;
		case VAR_UINT64:
			result = v.asUint64();
			break;
		default:
			cout << "ERROR! No conversion for type:" << v << endl;
			result = 0;
	}
	return result;
}

bool operator<(qpid::types::Variant a, qpid::types::Variant b) {
	return variantToDouble(a) < variantToDouble(b);
}
bool operator>(qpid::types::Variant a, qpid::types::Variant b) {
	return b < a;
}
bool operator<=(qpid::types::Variant a, qpid::types::Variant b) {
	return !(a>b);
}
bool operator>=(qpid::types::Variant a, qpid::types::Variant b) {
	return !(a<b);
}

// example event:eb68c4a5-364c-4fb8-9b13-7ea3a784081f:{action:{command:on, uuid:25090479-566d-4cef-877a-3e1927ed4af0}, criteria:{0:{comp:eq, lval:hour, rval:7}, 1:{comp:eq, lval:minute, rval:1}}, event:event.environment.timechanged, nesting:(criteria["0"] and criteria["1"])}


void eventHandler(std::string subject, qpid::types::Variant::Map content) {
	// ignore device announce events
	if (subject == "event.device.announce") return;
	// iterate event map and match for event name
	qpid::types::Variant::Map inventory = agoConnection->getInventory();
	for (qpid::types::Variant::Map::const_iterator it = eventmap.begin(); it!=eventmap.end(); it++) { 
		qpid::types::Variant::Map event;
		if (!(it->second.isVoid())) {
			event = it->second.asMap();
		} else {
			cout << "ERROR: eventmap entry is void" << endl;
		}
		if (event["event"] == subject) {
			// cout << "found matching event: " << event << endl;
			qpid::types::Variant::Map criteria; // this holds the criteria evaluation results for each criteria
			std::string nesting = event["nesting"].asString();
			if (!event["criteria"].isVoid()) for (qpid::types::Variant::Map::const_iterator crit = event["criteria"].asMap().begin(); crit!= event["criteria"].asMap().end(); crit++) {
				// cout << "criteria[" << crit->first << "] - " << crit->second << endl;
				qpid::types::Variant::Map element;
				if (!(crit->second.isVoid())) {
					element = crit->second.asMap();
				} else {
					cout << "ERROR: criteria element is void" << endl;
				}
				try {
					// cout << "LVAL: " << element["lval"] << endl;
					qpid::types::Variant::Map lvalmap;
					qpid::types::Variant lval;
					if (!element["lval"].isVoid()) {
						if (element["lval"].getType()==qpid::types::VAR_STRING) {
							// legacy eventmap entry
							lvalmap["type"] = "event";
							lvalmap["parameter"] = element["lval"];
						} else {
							lvalmap = element["lval"].asMap();
						}
					}
					// determine lval depending on type
					if (lvalmap["type"] == "variable") {
						qpid::types::Variant::Map variables;
						std::string name = lvalmap["name"];
						if (!inventory["variables"].isVoid()) variables = inventory["variables"].asMap();
						lval = variables[name];	

					} else if (lvalmap["type"] == "device") {
						std::string uuid = lvalmap["uuid"].asString();
						qpid::types::Variant::Map devices = inventory["devices"].asMap();
						qpid::types::Variant::Map device = devices[uuid].asMap();
						if (lvalmap["parameter"] == "state") {
							lval = device["state"];
						} else {
							qpid::types::Variant::Map values = device["values"].asMap();
							std::string parameter = lvalmap["parameter"].asString();
							qpid::types::Variant::Map value = values[parameter].asMap();
							lval = value["level"];
						}
					} else { // event
						lval = content[lvalmap["parameter"].asString()];
					}
					qpid::types::Variant rval = element["rval"];
					// cout << "lval: " << lval << " (" << getTypeName(lval.getType()) << ")" << endl;
					// cout << "rval: " << rval << " (" << getTypeName(rval.getType()) << ")" << endl;

					if (element["comp"] == "eq") {
						if (lval.getType()==qpid::types::VAR_STRING || rval.getType()==qpid::types::VAR_STRING) { // compare as string
							criteria[crit->first] = lval.asString() == rval.asString(); 
						} else {
							criteria[crit->first] = lval.isEqualTo(rval);
						}
					} else if (element["comp"] == "lt") {
						criteria[crit->first] = lval < rval;
					} else if (element["comp"] == "gt") {
						criteria[crit->first] = lval > rval;
					} else if (element["comp"] == "gte") {
						criteria[crit->first] = lval >= rval;
					} else if (element["comp"] == "lte") {
						criteria[crit->first] = lval <= rval;
					} else {
						criteria[crit->first] = false;
					}
					cout << lval << " " << element["comp"] << " " << rval << " : " <<  criteria[crit->first] << endl;
				} catch ( const std::exception& error) {
					stringstream errorstring;
					errorstring << error.what();
					cout << "ERROR, exception occured" << errorstring.str() << endl;
					criteria[crit->first] = false;
				}
				// this is for converted legacy scenario maps
				stringstream token; token << "criteria[\"" << crit->first << "\"]";
				stringstream boolval; boolval << criteria[crit->first];
				replaceString(nesting, token.str(), boolval.str()); 
				// new javascript editor sends criteria[x] not criteria["x"]
				stringstream token2; token2 << "criteria[" << crit->first << "]";
				stringstream boolval2; boolval2 << criteria[crit->first];
				replaceString(nesting, token2.str(), boolval2.str()); 
			}
			replaceString(nesting, "and", "&");
			replaceString(nesting, "or", "|");
			nesting += ";";
			// cout << "nesting prepared: " << nesting << endl;
			if (evaluateNesting(nesting)) {
				agoConnection->sendMessage(event["action"].asMap());
			}
		}	
	}

}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "eventcontroller") {
		if (content["command"] == "setevent") {
			try {
				cout << "setevent request" << endl;
				qpid::types::Variant::Map newevent = content["eventmap"].asMap();
				cout << "event content:" << newevent << endl;
				std::string eventuuid = content["event"].asString();
				if (eventuuid == "") eventuuid = generateUuid();
				cout << "event uuid:" << eventuuid << endl;
				eventmap[eventuuid] = newevent;
				agoConnection->addDevice(eventuuid.c_str(), "event", true);
				if (variantMapToJSONFile(eventmap, EVENTMAPFILE)) {
					returnval["result"] = 0;
					returnval["event"] = eventuuid;
				} else {
					returnval["result"] = -1;
				}
			} catch (qpid::types::InvalidConversion) {
                                returnval["result"] = -1;
                        } catch (...) {
                                returnval["result"] = -1;
				returnval["error"] = "exception";
			}
		} else if (content["command"] == "getevent") {
			try {
				std::string event = content["event"].asString();
				cout << "getevent request:" << event << endl;
				returnval["result"] = 0;
				returnval["eventmap"] = eventmap[event].asMap();
				returnval["event"] = event;
			} catch (qpid::types::InvalidConversion) {
				returnval["result"] = -1;
			}
                } else if (content["command"] == "delevent") {
			std::string event = content["event"].asString();
			cout << "delevent request:" << event << endl;
			returnval["result"] = -1;
			if (event != "") {
				qpid::types::Variant::Map::iterator it = eventmap.find(event);
				if (it != eventmap.end()) {
					cout << "removing ago device" << event << endl;
					agoConnection->removeDevice(it->first.c_str());
					eventmap.erase(it);
					if (variantMapToJSONFile(eventmap, EVENTMAPFILE)) {
						returnval["result"] = 0;
					}
				}
			}
                } 
	}
	return returnval;
}

int main(int argc, char **argv) {
	agoConnection = new AgoConnection("event");	
	cout << "parsing eventmap file" << endl;
	eventmap = jsonFileToVariantMap(EVENTMAPFILE);
	cout << "eventmap: " << eventmap << endl;
	cout << "adding controller" << endl;
	agoConnection->addDevice("eventcontroller", "eventcontroller");
	cout << "setting handlers" << endl;
	agoConnection->addHandler(commandHandler);
	agoConnection->addEventHandler(eventHandler);

	// cout  << eventmap;
	for (qpid::types::Variant::Map::const_iterator it = eventmap.begin(); it!=eventmap.end(); it++) {
		cout << "adding event:" << it->first << ":" << it->second << endl;	
		agoConnection->addDevice(it->first.c_str(), "event", true);
	}
	cout << "run()" << endl;
	agoConnection->run();
}
