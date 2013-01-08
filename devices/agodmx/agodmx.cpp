/*
	 Copyright (C) 2012 Harald Klein <hari@vt100.at>

	 This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
	 This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
	 of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

	 See the GNU General Public License for more details.

*/

#include <iostream>
#include <uuid/uuid.h>
#include <stdlib.h>

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include <tinyxml2.h>

#include "../agozwave/CDataFile.h"

#include <ola/DmxBuffer.h>
#include <ola/Logging.h>
#include <ola/StreamingClient.h>

using namespace qpid::messaging;
using namespace qpid::types;
using namespace tinyxml2;
using namespace std;


Sender sender;
Receiver receiver;
Session session;

Variant::Map deviceMap;

pthread_mutex_t mutexCon;
pthread_t listenerThread;


  // Create a new DmxBuffer to hold the data
  ola::DmxBuffer buffer;
  // set all channels to 0
//  buffer.Blackout();

  // create a new client and set the Error Closure
  ola::StreamingClient ola_client;


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
			XMLElement *channel = nextdevice->FirstChildElement( "channel" );
			if (channel) {
				XMLElement *nextchannel = channel;
				while (nextchannel != NULL) {
					printf("channel: %s - ",nextchannel->GetText());
					printf("type: %s\n",nextchannel->Attribute("type"));

					content[nextchannel->Attribute("type")]=nextchannel->GetText();
					nextchannel = nextchannel->NextSiblingElement();
				}
			}
			_deviceMap[nextdevice->Attribute("uuid")] = content;
			nextdevice = nextdevice->NextSiblingElement();
		}
	}
	return true;
}

/**
 * sets up the ola client
 */
bool ola_connect() {
	// turn on OLA logging
	ola::InitLogging(ola::OLA_LOG_WARN, ola::OLA_LOG_STDERR);

	// set all channels to 0
	buffer.Blackout();

	// Setup the client, this connects to the server
	if (!ola_client.Setup()) {
		printf("OLA client setup failed\n");
		return false;
	}
	return true;
}

/**
 * disconnects the ola client
 */
void ola_disconnect() {
	// close the connection
	ola_client.Stop();
}


/**
 * set a channel to off
 */
void ola_setChannel(int channel, int value) {
	printf("Setting channel %i to value %i\n", channel, value);
	buffer.SetChannel(channel, value);
}

/**
 * send buffer to ola
 */
bool ola_send(int universe = 0) {
	if (!ola_client.SendDmx(universe, buffer)) {
		printf("Send to dmx failed for universe %i\n", universe);
		return false;
	}
	printf("Send to dmx succesful for universe %i\n", universe);
	return true;
}

/**
 * set a device to a color
 */
void setDevice_color(Variant::Map device, int red=0, int green=0, int blue=0) {
	string channel_red = device["red"];
	string channel_green = device["green"];
	string channel_blue = device["blue"];
	ola_setChannel(atoi(channel_red.c_str()), red);
	ola_setChannel(atoi(channel_green.c_str()), green);
	ola_setChannel(atoi(channel_blue.c_str()), blue);
	ola_send();
}

/**
 * set device level 
 */
void setDevice_level(Variant::Map device, int level=0) {
	if (device["level"]) {
		string channel = device["level"];
		ola_setChannel(atoi(channel.c_str()), level);
		ola_send();
	} else {
	        string channel_red = device["red"];
        	string channel_green = device["green"];
	        string channel_blue = device["blue"];
		int red = (int) ( buffer.Get(atoi(channel_red.c_str())) * level / 100);
		int green = (int) ( buffer.Get(atoi(channel_green.c_str())) * level / 100);
		int blue = (int) ( buffer.Get(atoi(channel_blue.c_str())) * level / 100);
		printf("calculated RGB values for level %i are: red %i, green %i, blue %i\n");
		setDevice_color(device, red, green, blue);
	}
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
		content["devicetype"] = device["devicetype"].asString();
		content["uuid"] = it->first;
		encode(content, event);
		event.setSubject("event.device.announce");
		sender.send(event);
	}
}

int main(int argc, char **argv) {

	std::string broker;
	std::string eibdurl;
	std::string devicesFile;

	Variant::Map connectionOptions;

	// parse config
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

	t_Str szDevicesFile  = t_Str("");
	szDevicesFile = ExistingDF.GetString("devicesfile", "dmx");
	if ( szDevicesFile.size() == 0 )
		devicesFile="/etc/opt/agocontrol/dmx/channels.xml";
	else		
		devicesFile=szDevicesFile;

	// load xml file into map
	if (!loadDevices(devicesFile, deviceMap)) {
		printf("ERROR, can't load device xml\n");
		exit(-1);
	}

	// connect to OLA
	if (!ola_connect()) {
		printf("ERROR, can't connect to OLA\n");
		exit(-1);
	}


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

	pthread_mutex_init(&mutexCon,NULL);

	// announce devices to resolver
	reportDevices(deviceMap);



	while( true )
	{

		// Do stuff
		try{
			Variant::Map content;
			Message message = receiver.fetch(Duration::SECOND * 3);

			// workaround for bug qpid-3445
			if (message.getContent().size() < 4) {
				throw qpid::messaging::EncodingException("message too small");
			}

			decode(message, content);
			// std::cout << content << std::endl;
				session.acknowledge();
			if (content["command"] == "discover") {
				reportDevices(deviceMap);
			} else if (message.getSubject()=="") { // no subject, this should be a command
				// let's see if the command is for one of our devices
				for (Variant::Map::const_iterator it = deviceMap.begin(); it != deviceMap.end(); ++it) {
					if (content["uuid"] == it->first) {
						printf("received command  %s for device %s\n", content["command"].asString().c_str(), it->first.c_str());
						bool handled=true;
						if (content["command"] == "on") {
							setDevice_level(it->second.asMap(), 255);
						} else if (content["command"] == "off") {
							setDevice_level(it->second.asMap(), 0);
						} else if (content["command"] == "setlevel") {
							setDevice_level(it->second.asMap(), content["level"]);
						} else if (content["command"] == "setcolor") {
							setDevice_color(it->second.asMap(), content["red"], content["green"], content["blue"]);
						} else {
							handled=false;
						}
						if (handled) {	
							printf("Command handled ... \n");
						} else {
							printf("ERROR, received undhandled command\n");
						}
					}
				}
			}

		} catch(const NoMessageAvailable& error) {
			
		} catch(const std::exception& error) {
			std::cerr << error.what() << std::endl;
		}

	}

	ola_disconnect();

	try {
		connection.close();
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		connection.close();
		return 1;
	}
	
}
