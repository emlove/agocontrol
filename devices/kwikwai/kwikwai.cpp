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

#include "kwikwai.h"

using namespace std;

kwikwai::Kwikwai::Kwikwai(const char *hostname, const char *port) {
	struct addrinfo host_info;
	struct addrinfo *host_info_list;

	memset(&host_info, 0, sizeof host_info);

	host_info.ai_family = AF_UNSPEC;
	host_info.ai_socktype = SOCK_STREAM;

	int status = getaddrinfo(hostname, port, &host_info, &host_info_list);
	if (status != 0) {
		std::cout << "getaddrinfo error: " << gai_strerror(status) << std::endl;
		std::cout << "can't get address for " << hostname << " - aborting" << std::endl;
	}

	socketfd = socket(host_info_list->ai_family, host_info_list->ai_socktype, host_info_list->ai_protocol);
	if (socketfd == -1) {
		std::cout << "socket error" << std::endl ;
	}
	
	std::cout << "Connect()ing..."  << std::endl;
	status = connect(socketfd, host_info_list->ai_addr, host_info_list->ai_addrlen);
	if (status == -1) {
		std::cout << "connect error" << std::endl;
	}
	this->read();
}

int kwikwai::Kwikwai::write(std::string data) {
	unsigned int bytes_sent = send(socketfd, data.c_str(), data.size(), 0);
	if (bytes_sent != data.size()) {
		std::cout << "error sending data" << std::endl;
	} 
	return bytes_sent;
} 
std::string kwikwai::Kwikwai::read() {
	std::string result;
	char incoming_data_buffer[1000];
	int bytes_received;

	bytes_received  = recv(socketfd, incoming_data_buffer,1000, 0);
	if (bytes_received == 0) {
		std::cout << "host shut down." << std::endl ;
		return "";
	}
	if (bytes_received == -1) {
		std::cout << "receive error!" << std::endl ;
		return "";
	}
	result = string(incoming_data_buffer);
	result.erase(result.begin() + result.find("\r"),result.end());
	return result;
}

std::string kwikwai::Kwikwai::getVersion() {
	this->write("version:get\r\n");
	return this->read();
}

bool kwikwai::Kwikwai::cecSend(const char *command) {
	std::string tmpcommand = "cec:send A ";
	tmpcommand += command;
	tmpcommand += "\r\n";
	this->write(tmpcommand);
	std::string response = this->read();
	return response.size() ? true : false;
}
