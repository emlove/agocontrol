/*
     Copyright (C) 2009 Harald Klein <hari@vt100.at>

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

using namespace qpid::messaging;
using namespace qpid::types;
using namespace std;

#include <eibclient.h>
#include "Telegram.h"
#include "../agozwave/CDataFile.h"

Sender sender;
Receiver receiver;
Session session;

EIBConnection *eibcon;

int main(int argc, char **argv) {
	std::string broker;
	std::string eibdurl;

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
	szDevice = ExistingDF.GetString("url", "eibd");
	if ( szDevice.size() == 0 )
		eibdurl="ip:127.0.0.1";
	else		
		eibdurl= szDevice;

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

	printf("connecting to eibd\n");
	eibcon = EIBSocketURL(eibdurl.c_str());
	if (!eibcon) {
		printf("can't connect to url %s\n",eibdurl.c_str());
		exit(-1);
	}

	if (EIBOpen_GroupSocket (eibcon, 0) == -1)
	{
		EIBClose(eibcon);
		printf("can't open EIB Group Socket\n");
		exit(-1);
	}

	eibaddr_t dest = Telegram::stringtogaddr("0/0/32");
	
	Telegram *tg = new Telegram();
	tg->setGroupAddress(dest);
	tg->setDataFromChar((char)0xff);

	printf("sending telegram\n");
	bool result = tg->sendTo(eibcon);
	printf("Result: %i\n",result);


	while( true )
	{

		// Do stuff
		try{
			Variant::Map content;
			printf("fetching message\n");
			Message message = receiver.fetch(Duration::SECOND * 3);

			// workaround for bug qpid-3445
			if (message.getContent().size() < 4) {
				throw qpid::messaging::EncodingException("message too small");
			}

			decode(message, content);
			// std::cout << content << std::endl;
				session.acknowledge();
		} catch(const NoMessageAvailable& error) {
			
		} catch(const std::exception& error) {
			std::cerr << error.what() << std::endl;
		}

	}

	try {
		connection.close();
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		connection.close();
		return 1;
	}
	
}
