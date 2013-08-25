/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>
#include <sstream>

#include <sys/types.h>
#include <sys/stat.h>
#include <sys/socket.h>
#include <netdb.h>

#include <fcntl.h>
#include <string.h>

#include <termios.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#include "agoclient.h"

int irtrans_socket;
struct sockaddr_in server_addr;
struct hostent *host;


using namespace std;
using namespace agocontrol;

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	int internalid = atoi(content["internalid"].asString().c_str());
	printf("command: %s internal id: %i\n", content["command"].asString().c_str(), internalid);
	if (content["command"] == "sendir" ) {
		printf("sending IR code\n");
		string udpcommand;
		udpcommand.assign("sndccf ");
		udpcommand.append(content["ircode"].asString());
		sendto(irtrans_socket, udpcommand.c_str(), udpcommand.length(), 0, (struct sockaddr *)&server_addr, sizeof(struct sockaddr));
	}
	// TODO: Determine sane result code
	returnval["result"] = 0;
	return returnval;
}

int main(int argc, char **argv) {
	std::string hostname;
	std::string port;

	hostname=getConfigOption("irtrans_ethernet", "host", "192.168.80.12");
	port=getConfigOption("irtrans_ethernet", "port", "21000");

	host= (struct hostent *) gethostbyname((char *)hostname.c_str());

	if ((irtrans_socket = socket(AF_INET, SOCK_DGRAM, 0)) == -1) {
		perror("socket");
		return false;
	}

	server_addr.sin_family = AF_INET;

	// read the port from device data, TCP is a bit misleading, we do UDP
	server_addr.sin_port = htons(atoi(port.c_str()));

	server_addr.sin_addr = *((struct in_addr *)host->h_addr);
	bzero(&(server_addr.sin_zero),8);



	AgoConnection agoConnection = AgoConnection("irtrans_ethernet");		
	printf("connection to agocontrol established\n");

	agoConnection.addDevice("1", "infraredblaster");
	agoConnection.addHandler(commandHandler);

	printf("waiting for messages\n");
	agoConnection.run();

}

