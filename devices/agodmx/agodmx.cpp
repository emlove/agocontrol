/*
	 Copyright (C) 2012 Harald Klein <hari@vt100.at>

	 This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
	 This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
	 of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

	 See the GNU General Public License for more details.

*/

#include <iostream>
#include <stdlib.h>

#include <unistd.h>
#include <stdio.h>

#include <tinyxml2.h>

#include <ola/DmxBuffer.h>
#include <ola/Logging.h>
#include <ola/StreamingClient.h>

#include "agoclient.h"

using namespace qpid::types;
using namespace tinyxml2;
using namespace std;
using namespace agocontrol;


Variant::Map channelMap;
ola::DmxBuffer buffer;
ola::StreamingClient ola_client;
AgoConnection *agoConnection;

/**
 * parses the device XML file and creates a qpid::types::Variant::Map with the data
 */
bool loadChannels(string filename, Variant::Map& _channelMap) {
	XMLDocument channelsFile;
	int returncode;

	printf("trying to open channel file: %s\n", filename.c_str());
	returncode = channelsFile.LoadFile(filename.c_str());
	if (returncode != XML_NO_ERROR) {
		printf("error loading XML file, code: %i\n", returncode);
		return false;
	}

	printf("parsing file\n");
	XMLHandle docHandle(&channelsFile);
	XMLElement* device = docHandle.FirstChildElement( "devices" ).FirstChild().ToElement();
	if (device) {
		XMLElement *nextdevice = device;
		while (nextdevice != NULL) {
			Variant::Map content;

			printf("node: %s - ",nextdevice->Attribute("internalid"));
			printf("type: %s\n",nextdevice->Attribute("type"));

			content["internalid"] = nextdevice->Attribute("internalid");
			content["devicetype"] = nextdevice->Attribute("type");
			content["onlevel"] = 100;
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
			_channelMap[nextdevice->Attribute("internalid")] = content;
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
	return true;
}

/**
 * set a device to a color
 */
bool setDevice_color(Variant::Map device, int red=0, int green=0, int blue=0) {
	string channel_red = device["red"];
	string channel_green = device["green"];
	string channel_blue = device["blue"];
	ola_setChannel(atoi(channel_red.c_str()), red);
	ola_setChannel(atoi(channel_green.c_str()), green);
	ola_setChannel(atoi(channel_blue.c_str()), blue);
	return ola_send();
}

/**
 * set device level 
 */
bool setDevice_level(Variant::Map device, int level=0) {
	if (device["level"]) {
		string channel = device["level"];
		ola_setChannel(atoi(channel.c_str()), (int) ( 255.0 * level / 100 ));
		return ola_send();
	} else {
	        string channel_red = device["red"];
        	string channel_green = device["green"];
	        string channel_blue = device["blue"];
		int red = (int) ( buffer.Get(atoi(channel_red.c_str())) * level / 100);
		int green = (int) ( buffer.Get(atoi(channel_green.c_str())) * level / 100);
		int blue = (int) ( buffer.Get(atoi(channel_blue.c_str())) * level / 100);
		printf("calculated RGB values for level %i are: red %i, green %i, blue %i\n");
		return setDevice_color(device, red, green, blue);
	}
}

/**
 * set device strobe
 */
bool setDevice_strobe(Variant::Map device, int strobe=0) {
	if (device["strobe"]) {
		string channel = device["strobe"];
		ola_setChannel(atoi(channel.c_str()), (int) ( 255.0 * strobe / 100 ));
		return ola_send();
	} else {
		printf("Strobe command not supported on device\n");
                return false;
	}
}

/**
 * announces our devices in the channelmap to the resolver
 */
void reportDevices(Variant::Map channelmap) {
	for (Variant::Map::const_iterator it = channelmap.begin(); it != channelmap.end(); ++it) {
		Variant::Map device;

		device = it->second.asMap();
                agoConnection->addDevice(device["internalid"].asString().c_str(), device["devicetype"].asString().c_str());
	}
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map command) {
        bool handled = true;

        const char *internalid = command["internalid"].asString().c_str();

        qpid::types::Variant::Map returnval;
        returnval["result"] = 0;

        Variant::Map device = channelMap[internalid].asMap();

        if (command["command"] == "on") {
                if (setDevice_level(device, device["onlevel"])) {
                        agoConnection->emitEvent(internalid, "event.device.statechanged", device["onlevel"].asString().c_str(), "");
                }
        } else if (command["command"] == "off") {
                if (setDevice_level(device, 0)) {
                        agoConnection->emitEvent(internalid, "event.device.statechanged", "0", "");
                }
        } else if (command["command"] == "setlevel") {
                if (setDevice_level(device, command["level"])) {

                        Variant::Map content = device;
                        content["onlevel"] = command["level"].asString().c_str();
                        channelMap[internalid] = content;

                        agoConnection->emitEvent(internalid, "event.device.statechanged", command["level"].asString().c_str(), "");
                }
        } else if (command["command"] == "setcolor") {
                if (!setDevice_color(channelMap[internalid].asMap(), command["red"], command["green"], command["blue"])) {
                        handled = false;
                }
        } else if (command["command"] == "setstrobe") {
                if (!setDevice_strobe(channelMap[internalid].asMap(), command["strobe"])) {
                        handled = false;
                }
        } else {
                handled = false;
        }
        if (!handled) {
                returnval["result"] = 1;
                printf("ERROR, received undhandled command %s for node %s\n", command["command"].asString().c_str(), internalid); 
        }
        return returnval;
}


int main(int argc, char **argv) {
        std::string channelsFile, ola_server;

        channelsFile=getConfigOption("dmx", "channelsfile", CONFDIR "/dmx/channels.xml");
        ola_server=getConfigOption("dmx", "url", "ip:127.0.0.1");

	// load xml file into map
	if (!loadChannels(channelsFile, channelMap)) {
		printf("ERROR, can't load channel xml\n");
		exit(-1);
	}

	// connect to OLA
	if (!ola_connect()) {
		printf("ERROR, can't connect to OLA\n");
		exit(-1);
	}

        agoConnection = new AgoConnection("dmx");

        printf("connection to agocontrol established\n");

        reportDevices(channelMap);

        agoConnection->addHandler(commandHandler);

        printf("waiting for messages\n");
        agoConnection->run();

	ola_disconnect();
}
