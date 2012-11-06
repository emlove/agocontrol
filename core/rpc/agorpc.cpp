/*
     Copyright (C) 2012 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

     this is a lightweight RPC/HTTP interface for ago control for platforms where the regular cherrypy based admin interface is too slow
*/

#include <iostream>
#include "mongoose.h"

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#include <termios.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>

#include <sstream>

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include "../../devices/agozwave/CDataFile.h"

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

Receiver receiver;
Sender sender;
Session session;

struct mg_context       *ctx;

static void show_index(struct mg_connection *conn, const struct mg_request_info *request_info, void *user_data)
{
	mg_printf(conn, "%s",
		"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
		"<html><body><h1>Welcome to ago control</h1>");
	mg_printf(conn, "%s", "<a href=\"/inventory\">/inventory</a> - device inventory<br>");
	mg_printf(conn, "%s", "</body></html>");
}

static void command (struct mg_connection *conn, const struct mg_request_info *request_info, void *user_data) {
	char *uuid, *command, *level;
	Variant::Map agocommand;
	Message message;
	
	uuid = mg_get_var(conn, "uuid");
	command = mg_get_var(conn, "command");
	level = mg_get_var(conn, "level");

	agocommand["command"] = command;
	agocommand["uuid"] = uuid;
	if (level) {
		agocommand["level"] = level;
	}
	encode(agocommand, message);
	sender.send(message);
	
	mg_printf(conn, "%s", "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n");
	mg_printf(conn, "%s - %s", uuid, command);

}

static void inventory (struct mg_connection *conn, const struct mg_request_info *request_info, void *user_data) {
	Variant::Map agocommand;
	Variant::Map inventoryMap;	

	Message message;
	string inventory;
	
	agocommand["command"] = "inventory";
	encode(agocommand, message);

	Address responseQueue("#response-queue; {create:always, delete:always}");
	Receiver responseReceiver = session.createReceiver(responseQueue);
	message.setReplyTo(responseQueue);

	sender.send(message);
	Message response = responseReceiver.fetch();
	decode(response,inventoryMap);
/*	Variant::Map::iterator i = inventoryMap.find("schema");
	if (i == inventoryMap.end()) {
		inventory = i->second.asString();
	} */
	stringstream tmp;
	tmp << inventoryMap;
	inventory = tmp.str();

	mg_printf(conn, "%s", "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n");
	mg_printf(conn, "%s", inventory.c_str());

}

int main(int argc, char **argv) {
	string broker;

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

	// start web server
	ctx = mg_start();
	mg_set_option(ctx, "ports", "8008");
	mg_set_uri_callback(ctx, "/", &show_index, NULL);
	mg_set_uri_callback(ctx, "/command", &command, NULL);
	mg_set_uri_callback(ctx, "/inventory", &inventory, NULL);

	while (true) {
		sleep(10);
	}
}
