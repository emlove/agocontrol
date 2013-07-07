/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

     this is the core resolver component for ago control 
*/

#include <iostream>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#include <termios.h>
#include <malloc.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>

#include <sstream>
#include <map>
#include <deque>

#include <uuid/uuid.h>

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include "../../shared/agoclient.h"

#include "schema.h"
#include "inventory.h"

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;
using namespace agocontrol;


// qpid session and sender/receiver
Receiver receiver;
Sender sender;
Session session;
Connection agoConnection;

bool replyMessage(const Address& replyaddress, Message response) {
	if (replyaddress) {
		try {
			Session replysession = agoConnection.createSession();
			Sender replysender = session.createSender(replyaddress);
			replysender.send(response);
			replysession.close();
			return true;
		} catch(const std::exception& error) {
			clog << agocontrol::kLogErr << "cannot reply to request: " << error.what() << std::endl;
		}
	}
	return false;
}

bool sendMessage(const char *subject, qpid::types::Variant::Map content) {
        Message message;

        try {
                encode(content, message);
                message.setSubject(subject);
                sender.send(message);
        } catch(const std::exception& error) {
                std::cerr << error.what() << std::endl;
                return false;
        }

        return true;
}

bool emitNameEvent(const char *uuid, const char *eventType, const char *name) {
        Variant::Map content;
        content["name"] = name;
        content["uuid"] = uuid;
        return sendMessage(eventType, content);
}

bool emitFloorplanEvent(const char *uuid, const char *eventType, const char *floorplan, int x, int y) {
        Variant::Map content;
        content["uuid"] = uuid;
        content["floorplan"] = floorplan;
        content["x"] = x;
        content["y"] = y;
        return sendMessage(eventType, content);
}
void handleEvent(Variant::Map *device, string subject, Variant::Map *content);

int main(int argc, char **argv) {
	string broker;
	string port; 
	string schemafile;
	Variant::Map connectionOptions;

	clog.rdbuf(new agocontrol::Log("agoresolver", LOG_LOCAL0));
	clog << agocontrol::kLogNotice << "starting up" << std::endl;

	broker=getConfigOption("system", "broker", "localhost:5672");
	connectionOptions["username"]=getConfigOption("system", "username", "agocontrol");
	connectionOptions["password"]=getConfigOption("system", "password", "letmein");
	schemafile=getConfigOption("system", "schema", "/etc/opt/agocontrol/schema.yaml");

	connectionOptions["reconnect"] = "true";

	clog << agocontrol::kLogDebug << "connecting to broker" << std::endl;
	agoConnection = Connection(broker, connectionOptions);
	try {
		agoConnection.open(); 
		session = agoConnection.createSession(); 
		receiver = session.createReceiver("agocontrol; {create: always, node: {type: topic}}"); 
		sender = session.createSender("agocontrol; {create: always, node: {type: topic}}"); 
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		agoConnection.close();
		printf("could not startup\n");
		return 1;
	}


	Variant::Map inventory; // used to hold device registrations
	Variant::Map schema;  

	clog << agocontrol::kLogDebug << "parsing schema file" << std::endl;
	schema = parseSchema(schemafile.c_str());

	clog << agocontrol::kLogDebug << "reading inventory" << std::endl;
	Inventory inv("/etc/opt/agocontrol/inventory.db");
	
	// discover devices
	clog << agocontrol::kLogDebug << "discovering devices" << std::endl;
	Variant::Map discovercmd;
	discovercmd["command"] = "discover";
	Message discovermsg;
	try {
		encode(discovercmd, discovermsg);
		sender.send(discovermsg);
	} catch(const std::exception& error) {
		clog << agocontrol::kLogEmerg << "can't discover devices" << std::endl;
		return 1;
	}

	while (true) {
		try{
			Variant::Map content;
			string subject;
			Message message = receiver.fetch(Duration::SECOND * 3);
			// clog << agocontrol::kLogDebug << "acknowledge message" << std::endl;
			session.acknowledge();

			// workaround for bug qpid-3445
			if (message.getContent().size() < 4) {
				clog << agocontrol::kLogDebug << "working aroung qpid bug 3445" << std::endl;
				throw qpid::messaging::EncodingException("message too small");
			}

			// clog << agocontrol::kLogDebug << "decoding message" << std::endl;
			decode(message, content);
			subject = message.getSubject();
			// clog << agocontrol::kLogDebug << "subject:" << subject << "size:" << subject.size() << std::endl;

			// test if it is an event
			if (subject.size()>0) {
				if (subject == "event.device.announce") {
					string uuid = content["uuid"];
					if (uuid != "") {
						// clog << agocontrol::kLogDebug << "preparing device: uuid="  << uuid << std::endl;
						Variant::Map device;
						Variant::Map values;
						device["devicetype"]=content["devicetype"].asString();
						device["internalid"]=content["internalid"].asString();
						device["handled-by"]=content["handled-by"].asString();
						// clog << agocontrol::kLogDebug << "getting name from inventory" << endl;
						device["name"]=inv.getdevicename(content["uuid"].asString());
						device["name"].setEncoding("utf8");
						// clog << agocontrol::kLogDebug << "getting room from inventory" << endl;
						device["room"]=inv.getdeviceroom(content["uuid"].asString()); 
						device["room"].setEncoding("utf8");
						device["state"]="0";
						device["state"].setEncoding("utf8");
						device["values"]=values;
						clog << agocontrol::kLogDebug << "adding device: uuid="  << uuid  << " type: " << device["devicetype"].asString() << std::endl;
						inventory[uuid] = device;
					}
				} else if (subject == "event.device.remove") {
					string uuid = content["uuid"];
					if (uuid != "") {
						clog << agocontrol::kLogDebug << "removing device: uuid="  << uuid  << std::endl;
						Variant::Map::iterator it = inventory.find(uuid);
						if (it != inventory.end()) {
							inventory.erase(it);
						}
					}
				} else {
					if (content["uuid"].asString() != "") {
						string uuid = content["uuid"];
						// see if we have that device in the inventory already, if yes handle the event
						if (inventory.find(uuid) != inventory.end()) handleEvent(&inventory[uuid].asMap(), subject, &content);
					}

				}
				//printf("received event: %s\n", subject.c_str());	

			} else {
				// this is a command
				if (content["command"] == "inventory") {
					clog << agocontrol::kLogDebug << "responding to inventory request" << std::endl;
					Variant::Map reply;
					reply["inventory"] = inventory;
					reply["schema"] = schema;	
					reply["rooms"] = inv.getrooms();
					reply["floorplans"] = inv.getfloorplans();

					// cout << agocontrol::kLogDebug << "inv: " << inventory << std::endl;
					Message response;
					encode(reply, response);
					replyMessage(message.getReplyTo(), response);
				} else if (content["command"] == "setroomname") {
					string uuid = content["uuid"];
					// if no uuid is provided, we need to generate one for a new room
					if (uuid == "") uuid = generateUuid();
					inv.setroomname(uuid, content["name"]);
					Message response(uuid);
					replyMessage(message.getReplyTo(), response);
					emitNameEvent(uuid.c_str(), "event.system.roomnamechanged", content["name"].asString().c_str());
				} else if (content["command"] == "setdeviceroom") {
					string result;
					if ((content["uuid"].asString() != "") && (inv.setdeviceroom(content["uuid"], content["room"]) == 0)) {
						result = "OK"; // TODO: unify responses
						// update room in local device map
						Variant::Map *device;
						string room = inv.getdeviceroom(content["uuid"]);
						string uuid = content["uuid"];
						device = &inventory[uuid].asMap();
						(*device)["room"]= room;
					} else {
						result = "ERR"; // TODO: unify responses
					}
					Message response(result);
					replyMessage(message.getReplyTo(), response);
				} else if (content["command"] == "setdevicename") {
					string result;
					if ((content["uuid"].asString() != "") && (inv.setdevicename(content["uuid"], content["name"]) == 0)) {
						result = "OK"; // TODO: unify responses
                                                // update name in local device map
                                                Variant::Map *device;
                                                string name = inv.getdevicename(content["uuid"]);
                                                string uuid = content["uuid"];
                                                device = &inventory[uuid].asMap();
                                                (*device)["name"]= name;
                                        } else {
                                                result = "ERR"; // TODO: unify responses
                                        }
					Message response(result);
					replyMessage(message.getReplyTo(), response);
					emitNameEvent(content["uuid"].asString().c_str(), "event.system.devicenamechanged", content["name"].asString().c_str());

				} else if (content["command"] == "deleteroom") {
					string result;
					if (inv.deleteroom(content["uuid"]) == 0) {
						result = "OK";
					} else {
						result = "ERR";
					}
					Message response(result);
					replyMessage(message.getReplyTo(), response);
				} else if (content["command"] == "setfloorplanname") {
					string uuid = content["uuid"];
					// if no uuid is provided, we need to generate one for a new floorplan
					if (uuid == "") uuid = generateUuid();
					inv.setfloorplanname(uuid, content["name"]);
					Message response(uuid);
					replyMessage(message.getReplyTo(), response);
					emitNameEvent(content["uuid"].asString().c_str(), "event.system.floorplannamechanged", content["name"].asString().c_str());
				} else if (content["command"] == "setdevicefloorplan") {
					string result;
					if ((content["uuid"].asString() != "") && (inv.setdevicefloorplan(content["uuid"], content["floorplan"], content["x"], content["y"]) == 0)) {
						result = "OK"; // TODO: unify responses
					} else {
						result = "ERR"; // TODO: unify responses
					}
					Message response(result);
					replyMessage(message.getReplyTo(), response);
					emitFloorplanEvent(content["uuid"].asString().c_str(), "event.system.floorplandevicechanged", content["floorplan"].asString().c_str(), content["x"], content["y"]);

				} else if (content["command"] == "deletefloorplan") {
					string result;
					if (inv.deletefloorplan(content["uuid"]) == 0) {
						result = "OK";
					} else {
						result = "ERR";
					}
					Message response(result);
					replyMessage(message.getReplyTo(), response);
				}
			}

		} catch(const NoMessageAvailable& error) {
			
		} catch(const std::exception& error) {
			clog << agocontrol::kLogCrit << "Unhandled exception: " << error.what() << std::endl;
			if (session.hasError()) {
				clog << agocontrol::kLogCrit << "Session has error, recreating" << std::endl;
				session.close();
				session = agoConnection.createSession(); 
				receiver = session.createReceiver("agocontrol; {create: always, node: {type: topic}}"); 
				sender = session.createSender("agocontrol; {create: always, node: {type: topic}}"); 
			}
		}
	}

}

// helper to determine last element
template <typename Iter>
Iter next(Iter iter)
{
	return ++iter;
}

string valuesToString(Variant::Map *values) {
	string result;
	for (Variant::Map::const_iterator it = values->begin(); it != values->end(); ++it) {
		result += it->second.asString();
		if ((it != values->end()) && (next(it) != values->end())) result += "/";	
	}
	return result;
}

void handleEvent(Variant::Map *device, string subject, Variant::Map *content) {
	Variant::Map *values;
	values = &(*device)["values"].asMap();
	if (subject == "event.device.statechanged") {// event.device.statechange
		(*values)["state"] = (*content)["level"];
		(*device)["state"]  = (*content)["level"];
		(*device)["state"].setEncoding("utf8");
		// (*device)["state"]  = valuesToString(values);
	} else if ((subject.find("event.environment.") != std::string::npos) && (subject.find("changed")!= std::string::npos)) {
		Variant::Map value;
		string quantity = subject;
		quantity.erase(quantity.begin(),quantity.begin()+18);
		quantity.erase(quantity.end()-7,quantity.end());

		value["unit"] = (*content)["unit"];
		value["level"] = (*content)["level"];
		(*values)[quantity] = value;
	}
}
