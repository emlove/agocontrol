/*
 * aGoControl messagesend - CLI for sending commands
 */

#include <stdlib.h> 
#include <stdio.h>
#include <errno.h>

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <vector>
#include <ctime>

#include "agoclient.h"

using namespace std;
using namespace agocontrol;

using std::stringstream;
using std::string;

static bool nameval(const std::string& in, std::string& name, std::string& value) {
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

int main(int argc, char **argv) {
	AgoConnection agoConnection = AgoConnection("messagesend");		

	qpid::types::Variant::Map content;
	for (int i=1;i<argc;i++) {
		string name, value;
		if (nameval(string(argv[i]),name, value)) {
			content[name]=value;
		}
	}
	cout << "Sending message: " << content << endl;
	agoConnection.sendMessage(content);
}


