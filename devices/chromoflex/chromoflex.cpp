/*
     Copyright (C) 2009 Harald Klein <hari@vt100.at>

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

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

Sender sender;

int fd; // file desc for device
unsigned short   usp_crc; // initialise per packet with $FFFF.
int increment;
int speed;

void process_crc(unsigned char ucData) {
      int i;
      usp_crc^=ucData;
      for(i=0;i<8;i++){ // Process each Bit
             if(usp_crc&1){ usp_crc >>=1; usp_crc^=0xA001;}
             else{          usp_crc >>=1; }
      }

}
void reportDevices(std::string uuid) {
	Variant::Map content;
	Message event;
	try {
		content["uuid"] = uuid;
		content["product"] = "Chromoflex USP3";
		content["manufacturer"] = "Xeroflex";
		content["internal-id"] = "0";
		content["devicetype"] = "dimmerrgb";
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
	szDevice = ExistingDF.GetString("device", "chromoflex");
	if ( szDevice.size() == 0 )
		devicefile="/dev/ttyS_01";
	else		
		devicefile= szDevice;

	t_Str szUuid = t_Str("");
	szUuid = ExistingDF.GetString("uuid", "chromoflex");
	if ( szUuid.size() == 0 )
		myuuid="489ad103-0dfc-4023-aac2-10d65b4bab0d";
	else		
		myuuid= szUuid;

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

	fd = open(devicefile.c_str(), O_RDWR);
	unsigned char buf[1024];

	increment=1;
	speed=1;

	// init crc
	usp_crc = 0xffff;

	// disable any programs on the units
	buf[0]=0xca; // preamble
	buf[1]=0x00; // broadcast
	buf[2]=0x00; // broadcast
	buf[3]=0x00; // broadcast
	buf[4]=0x00; // length 
	buf[5]=0x02; // length
	buf[6]=0x7e; // 7e == write register
	buf[7]=18; // register addr
	buf[8]=0x01; // disable internal programs
	for (int i = 0; i < 9; i++) process_crc(buf[i]);
	buf[9] = (usp_crc >> 8);
	buf[10] = (usp_crc & 0xff);

	// setup B9600 8N1 first
	struct termios tio;
	tcgetattr(fd, &tio);
	tio.c_cflag = B9600 | CS8 | CLOCAL | CREAD;
	tcflush(fd, TCIFLUSH);
	tcsetattr(fd,TCSANOW,&tio);

	if (write (fd, buf, 11) != 11) {
		printf("ERROR: can't open device %s:%i\n",devicefile.c_str(),fd);
		exit (1);
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

	reportDevices(myuuid);
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
				reportDevices(myuuid);
			}

			if (content["uuid"] == myuuid) {
				printf("received command for our uuid\n");
				int red = 0;
				int green = 0;
				int blue = 0;
				unsigned char buf[1024];

				int level = 0;
				if (content["command"] == "on" ) {
					red = 255; green = 255; blue=255;
				} else if (content["command"] == "off") {
					red = 0; green = 0; blue=0;
				} else if (content["command"] == "setlevel") {
					level = content["level"];
					red = green = blue = (int) ( 255.0 * level / 100 );
				} else if (content["command"] == "setcolor") {
					red = content["red"];		
					green = content["green"];		
					blue = content["blue"];		
				}

				// assemble frame
				buf[0]=0xca; // preamble
				buf[1]=0x00; // broadcast
				buf[2]=0x00; // broadcast
				buf[3]=0x00; // broadcast
				buf[4]=0x00; // length 
				buf[5]=0x08; // length
				buf[6]=0x7e; // 7e == effect color
				buf[7]=0x04; // register addr
				buf[8]=red; // R
				buf[9]=green; // G
				buf[10]=blue; // B
				buf[11]=0x00; // X
				buf[12]=increment; // reg 8 - red increment
				buf[13]=increment; // reg 9 - green increment
				buf[14]=increment; // reg 10 - blue increment

				// calc crc16
				usp_crc = 0xffff;
				for (int i = 0; i < 15; i++) process_crc(buf[i]);

				buf[15] = (usp_crc >> 8);
				buf[16] = (usp_crc & 0xff);

				printf("sending command...\n");
				if (write (fd, buf, 17) != 17) {
					printf ("Write error: %s", strerror(errno ));
					try {
						connection.close();
					} catch(const std::exception& error) {
						std::cerr << error.what() << std::endl;
						connection.close();
					}
					exit(1);
				}
				const Address& replyaddress = message.getReplyTo();
				if (replyaddress) {
					Sender replysender = session.createSender(replyaddress);
					Message response("ACK");
					replysender.send(response);
				} 
			}
		// } catch(const NoMessageAvailable::NoMessageAvailable& error) {
		} catch(const std::exception& error) {
			std::cerr << error.what() << std::endl;
		}

	}
}

