/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#include <termios.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include <uuid/uuid.h>
#include <stdlib.h>

#include "../agozwave/CDataFile.h"

#include "rain8.h"

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

Sender sender;

void reportDevices(std::string uuid, std::string id) {
	Variant::Map content;
	Message event;
	try {
		content["uuid"] = uuid;
		content["product"] = "Rain8net valve";
		content["manufacturer"] = "WGL";
		content["internal-id"] = id;
		content["devicetype"] = "valve";
		encode(content, event);
		event.setSubject("event.device.announce");
		sender.send(event);
	} catch(const std::exception& error) {
		std::cout << error.what() << std::endl;
	}
}

int main(int argc, char **argv) {
	std::string broker;
	std::string devicefile;
	std::string myuuid;

	rain8net rain8;
	int rc;

	Variant::Map connectionOptions;

	// parse config
	CDataFile ExistingDF("/etc/opt/agocontrol/config.ini");

	t_Str szBroker  = t_Str("");
	szBroker = ExistingDF.GetString("broker", "system");
	if ( szBroker.size() == 0 )
		broker="localhost:5672";
	else		
		broker= szBroker;

	t_Str szDevice = t_Str("");
	szDevice = ExistingDF.GetString("device", "rain8net");
	if ( szDevice.size() == 0 )
		devicefile="/dev/ttyS_01";
	else		
		devicefile= szDevice;

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

	connectionOptions["reconnect"] = "true";

	Receiver receiver;
	Session session;

	if (rain8.init(devicefile.c_str()) != 0) {
		printf("can't open rainnet device %s\n", devicefile.c_str());
		exit(1);
	}
	if ((rc = rain8.comCheck()) != 0) {
		printf("can't talk to rainnet device %s, comcheck failed: %i\n", devicefile.c_str(),rc);
		exit(1);
	}
	printf("connection to rain8net established\n");
	unsigned char status;
	if (rain8.getStatus(1,status) == 0) {
		printf("can't get zone status, aborting\n");
		exit(1);
	} else {
		printf("Zone status: 8:%d 7:%d 6:%d 5:%d 4:%d 3:%d 2:%d 1:%d", (status & 128)?1:0, (status & 64)?1:0, (status &32)?1:0,(status&16)?1:0,(status&8)?1:0,(status&4)?1:0,(status&2)?1:0,(status&1)?1:0);
	}

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
	myuuid = "1234";
	reportDevices(myuuid, string("1"));

	while (true) {
		try {
			Variant::Map content;
			Message message = receiver.fetch(Duration::SECOND * 3);

			// workaround for bug qpid-3445
			if (message.getContent().size() < 4) {
				throw qpid::messaging::EncodingException("message too small");
			}

			decode(message, content);
			// std::cout << content << std::endl;

			if (content["command"] == "discover") {
				reportDevices(myuuid, string("1"));
			}

			if (content["uuid"] == myuuid) {
				printf("received command for our uuid\n");
				int valve = 1;
				if (content["command"] == "on" ) {
					if (rain8.zoneOn(1,valve) != 0) {
						printf("can't switch on\n");
					} else {
						printf("switched on\n");
					}
				} else if (content["command"] == "off") {
					if (rain8.zoneOff(1,valve) != 0) {
						printf("can't switch off\n");
					} else {
						printf("switched off\n");
					}
				}

				const Address& replyaddress = message.getReplyTo();
				if (replyaddress) {
					Sender replysender = session.createSender(replyaddress);
					Message response("ACK");
					replysender.send(response);
				} 
			}
		} catch(const NoMessageAvailable& error) {
		} catch(const std::exception& error) {
			std::cerr << error.what() << std::endl;
		}

	}
}

