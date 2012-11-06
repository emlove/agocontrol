/*
 * aGoControl messagesend - CLI for sending commands
 */

#include <stdlib.h> 
#include <stdio.h>
#include <errno.h>

#include <qpid/messaging/Session.h>
#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Address.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Message.h>

#include <qpid/types/Variant.h>

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <vector>
#include <ctime>

#include "../../devices/agozwave/CDataFile.h"


using namespace qpid::messaging;
using namespace qpid::types;

using std::stringstream;
using std::string;

    static bool nameval(const std::string& in, std::string& name, std::string& value)
    {
        std::string::size_type i = in.find("=");
        if (i == std::string::npos) {
            name = in;
            return false;
        } else {
            name = in.substr(0, i);
            if (i+1 < in.size()) {
                value = in.substr(i+1);
                return true;
            } else {
                return false;
            }
        }
    }


int main(int argc, char **argv)
{
		for (int i=0;i<argc;i++) {
			printf("%i %c\n",i,argv[i]);
		}
        std::string broker;
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
            Session session = connection.createSession();
            Sender sender = session.createSender("agocontrol; {create: always, node: {type: topic}}");
 
            Message message;
		Variant::Map content;
		std::string value;
		value = "";
		for (int i=1;i<argc;i++) {
			printf("%i %c\n",i,argv[i]);
			string name;
			name = "uuid";
			if (nameval(string(argv[i]),name, value)) {
				content["uuid"]=value;
			}
			name = "command";
			if (nameval(string(argv[i]),name, value)) {
				content["command"]=value;
			}
		}
		encode(content, message);
                sender.send(message, true);
		session.close();
		connection.close();
        } catch(const std::exception& error) {
		std::cout << error.what() << std::endl;
		connection.close();
		exit(1);
        }
	exit(0);
}


