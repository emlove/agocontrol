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

#include "../../devices/agozwave/CDataFile.h"

#include "schema.h"
#include "inventory.h"

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

// qpid session and sender/receiver
Receiver receiver;
Sender sender;
Session session;

// generates a uuid as string via libuuid
string generateUuid() {
	string strUuid;
	char *name;
	if ((name=(char*)malloc(38)) != NULL) {
		uuid_t tmpuuid;
		name[0]=0;
		uuid_generate(tmpuuid);
		uuid_unparse(tmpuuid,name);
		strUuid = string(name);
		free(name);
	}
	return strUuid;
}

void handleEvent(Variant::Map *device, string subject, Variant::Map *content);

int main(int argc, char **argv) {
	string broker;
	string port; 
	string schemafile;

	Variant::Map connectionOptions;
	CDataFile ExistingDF("/etc/opt/agocontrol/config.ini");

	t_Str szBroker  = t_Str("");
	szBroker = ExistingDF.GetString("broker", "system");
	if ( szBroker.size() == 0 )
		broker="localhost:5672";
	else		
		broker= szBroker;
	t_Str szUsername  = t_Str("");
	szUsername = ExistingDF.GetString("username", "system");
	if ( szUsername.size() == 0 )
		connectionOptions["username"]="agocontrol";
	else		
		connectionOptions["username"] = szUsername;

	t_Str szPassword  = t_Str("");
	szPassword = ExistingDF.GetString("password", "system");
	if ( szPassword.size() == 0 )
		connectionOptions["password"]="letmein";
	else		
		connectionOptions["password"]=szPassword;

	t_Str szSchemafile  = t_Str("");
	szSchemafile = ExistingDF.GetString("schema", "system");
	if ( szSchemafile.size() == 0 )
		schemafile = "/etc/opt/agocontrol/schema.yaml";
	else		
		schemafile =szPassword;


	connectionOptions["reconnect"] = "true";


	Connection connection(broker, connectionOptions);
	try {
		connection.open(); 
		session = connection.createSession(); 
		receiver = session.createReceiver("agocontrol; {create: always, node: {type: topic}}"); 
		sender = session.createSender("agocontrol; {create: always, node: {type: topic}}"); 
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		connection.close();
		printf("could not startup\n");
		return 1;
	}


	Variant::Map inventory; // used to hold device registrations
	Variant::Map schema;  
	schema = parseSchema(schemafile.c_str());

	Inventory inv("/etc/opt/agocontrol/inventory.db");
	
	// discover devices
	Variant::Map discovercmd;
	discovercmd["command"] = "discover";
	Message discovermsg;
	encode(discovercmd, discovermsg);
	try {
		sender.send(discovermsg);
	} catch(const std::exception& error) {
		printf("could not send discover msg\n");
		return 1;
	}

	while (true) {
		try{
			Variant::Map content;
			string subject;
			Message message = receiver.fetch(Duration::SECOND * 3);
			session.acknowledge();

			// workaround for bug qpid-3445
			if (message.getContent().size() < 4) {
				throw qpid::messaging::EncodingException("message too small");
			}
			decode(message, content);
			subject = message.getSubject();

			// test if it is an event
			if (subject.size()>0) {
				if (subject == "event.device.announce") {
					string uuid = content["uuid"];
					if (uuid != "") {
						printf("adding device: uuid=%s\n", uuid.c_str());
						Variant::Map device;
						Variant::Map values;
						device["devicetype"]=content["devicetype"];
						device["name"]=inv.getdevicename(content["uuid"].asString());
						device["room"]=inv.getdeviceroom(content["uuid"].asString()); 
						device["state"]="-";
						device["values"]=values;
						inventory[uuid] = device;
					}
				} else {
					if (content["uuid"].asString() != "") {
						string uuid = content["uuid"];
						handleEvent(&inventory[uuid].asMap(), subject, &content);
					}

				}
				//printf("received event: %s\n", subject.c_str());	

			} else {
				// this is a command
				if (content["command"] == "inventory") {
					Variant::Map reply;
					Variant::Map rooms;
					reply["inventory"] = inventory;
					reply["schema"] = schema;	
					reply["rooms"] = inv.getrooms();

					const Address& replyaddress = message.getReplyTo();	
					if (replyaddress) {
						Sender replysender = session.createSender(replyaddress);
						Message response;
						encode(reply, response);
						try {
							replysender.send(response);
						} catch(const std::exception& error) {
							printf("could not send reply\n");
						}
					}
				} else if (content["command"] == "setroomname") {
					string uuid = content["uuid"];
					// if no uuid is provided, we need to generate one for a new room
					if (uuid == "") uuid = generateUuid();
					inv.setroomname(uuid, content["name"]);
					const Address& replyaddress = message.getReplyTo();	
					if (replyaddress) {
						Sender replysender = session.createSender(replyaddress);
						// the web admin expects us to just return the plain uuid
						Message response(uuid);
						try {
							replysender.send(response);
						} catch(const std::exception& error) {
							printf("could not send reply\n");
						}
					}
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
					const Address& replyaddress = message.getReplyTo();	
					if (replyaddress) {
						Sender replysender = session.createSender(replyaddress);
						Message response(result);
						try {
							replysender.send(response);
						} catch(const std::exception& error) {
							printf("could not send reply\n");
						}
					}
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
                                        const Address& replyaddress = message.getReplyTo();
                                        if (replyaddress) {
                                                Sender replysender = session.createSender(replyaddress);
                                                Message response(result);
                                                try {
                                                        replysender.send(response);
                                                } catch(const std::exception& error) {
                                                        printf("could not send reply\n");
                                                }
                                        }

				} else if (content["command"] == "deleteroom") {
					string result;
					if (inv.deleteroom(content["uuid"]) == 0) {
						result = "OK";
					} else {
						result = "ERR";
					}
                                        const Address& replyaddress = message.getReplyTo();
                                        if (replyaddress) {
                                                Sender replysender = session.createSender(replyaddress);
                                                Message response(result);
                                                try {
                                                        replysender.send(response);
                                                } catch(const std::exception& error) {
                                                        printf("could not send reply\n");
                                                }
                                        }
				} 
			}

		} catch(const NoMessageAvailable& error) {
			
		} catch(const std::exception& error) {
			std::cerr << error.what() << std::endl;
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
	if (subject == "event.device.statechanged") {// event.device.statechange
		Variant::Map *values;
		values = &(*device)["values"].asMap();
		(*values)["state"] = (*content)["level"];
		(*device)["state"]  = valuesToString(values);
	} else if (subject == "event.environment.temperaturechanged") {
		Variant::Map *values;
		string elem = "values";
		values = &(*device)[elem].asMap();
		(*values)["temperature"] = (*content)["level"];
		(*device)["state"]  = valuesToString(values);
	} else if (subject == "event.environment.humiditychanged") {
		Variant::Map *values;
		string elem = "values";
		values = &(*device)[elem].asMap();
		(*values)["humidity"] = (*content)["level"];
		(*device)["state"]  = valuesToString(values);
	}
}
