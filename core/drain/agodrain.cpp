#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
using namespace std;

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>
using namespace qpid::types;
using namespace qpid::messaging;

#include "agoclient.h"
using namespace agocontrol;

// qpid session and sender/receiver
Receiver receiver;
Sender sender;
Session session;
Connection *connection;


int main(int argc, char **argv) {
        string broker;

        Variant::Map connectionOptions;
        broker=getConfigOption("system", "broker", "localhost:5672");
        connectionOptions["username"]=getConfigOption("system", "username", "agocontrol");
        connectionOptions["password"]=getConfigOption("system", "password", "letmein");

        connectionOptions["reconnect"] = "true";

        connection = new Connection(broker, connectionOptions);
        try {
                connection->open(); 
                session = connection->createSession(); 
                receiver = session.createReceiver("agocontrol; {create: always, node: {type: topic}}"); 
                sender = session.createSender("agocontrol; {create: always, node: {type: topic}}"); 
        } catch(const std::exception& error) {
                std::cerr << error.what() << std::endl;
                connection->close();
                printf("could not startup\n");
                return 1;
        }


        while (true) {
                try{
                        Message message = receiver.fetch(Duration::SECOND * 3);
                        std::cout << "Message(properties=" << message.getProperties() << ", content='" ;
                        if (message.getContentType() == "amqp/map") {
                                Variant::Map map;
                                decode(message, map);
                                std::cout << map;
                        } else {
                                std::cout << message.getContent();
                        }
                        std::cout  << "')" << std::endl;
                        session.acknowledge(message);

                } catch(const NoMessageAvailable& error) {
                        
                } catch(const std::exception& error) {
                        std::cerr << error.what() << std::endl;
                        usleep(50);
                }
        }

}
