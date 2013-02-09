#include "agoclient.h"

using namespace agocontrol;

int main(int argc, char **argv) {
	qpid::types::Variant::Map testmap;
	testmap["key"] = "value";
	std::string teststring = variantMapToJSONString(testmap);
	printf("json test: %s\n",teststring.c_str());
	testmap = jsonStringToVariantMap(teststring);		
	printf("accessing testmap[\"key\"]: %s\n",testmap["key"].asString().c_str());
	printf("uuid test: %s\n",generateUuid().c_str());
		
	

}
