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
	if (argc < 2) {
		cout << "Usage example: " << argv[0] << " uuid=ca9424e6-406d-4144-8931-584046eaaa34 command=setlevel level=50" << endl;
		return -1;
	}
	AgoConnection agoConnection = AgoConnection("messagesend");		

	qpid::types::Variant::Map content;
	std::string subject;
	subject = "";
	for (int i=1;i<argc;i++) {
		string name, value;
		if (nameval(string(argv[i]),name, value)) {
			if (name == "subject") {
				subject = value;
			} else {
				content[name]=value;
			}
		}
	}
	cout << "Sending message: " << content << endl;
	qpid::types::Variant::Map replyMap = agoConnection.sendMessageReply(subject.c_str(), content);
	cout << "Reply: " << replyMap << endl;
}


