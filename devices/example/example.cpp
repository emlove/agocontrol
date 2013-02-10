#include "agoclient.h"

using namespace agocontrol;

std::string commandHandler(qpid::types::Variant::Map command) {
	if (command["command"] == "on") {
		printf("Switch %s ON\n", command["internalid"].asString().c_str());
		return "255";
	} else if (command["command"] == "off") {
		printf("Switch %s OFF\n", command["internalid"].asString().c_str());
		return "0";
	}	
}

int main(int argc, char **argv) {
	AgoConnection agoConnection = AgoConnection("example");
	printf("connection established\n");
	agoConnection.addDevice("123", "dimmer");
	agoConnection.addDevice("124", "switch");
	agoConnection.addHandler(commandHandler);
	agoConnection.run();
}
