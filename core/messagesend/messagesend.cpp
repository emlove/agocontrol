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

using namespace std;
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
			printf("%i %s\n",i,argv[i]);
		}

		Variant::Map content;
		std::string value;
		value = "";
		for (int i=1;i<argc;i++) {
			printf("%i %s\n",i,argv[i]);
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
	cout << content << endl;
	exit(0);
}


