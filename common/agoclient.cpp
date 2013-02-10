#include <string>

#include <stdio.h>
#include <unistd.h>

#include <jsoncpp/json/reader.h>
#include "agoclient.h"

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

// helper to determine last element
template <typename Iter>
Iter next(Iter iter)
{
    return ++iter;
}

std::string agocontrol::variantMapToJSONString(qpid::types::Variant::Map map) {
	string result;
	result += "{";
	for (Variant::Map::const_iterator it = map.begin(); it != map.end(); ++it) {
		result += "\""+ it->first + "\":";
		switch (it->second.getType()) {
			case VAR_MAP:
				result += variantMapToJSONString(it->second.asMap());
				break;
			case VAR_LIST:
				result += variantListToJSONString(it->second.asList());
				break;
			case VAR_STRING:
				result += "\"" +  it->second.asString() + "\"";
				break;
			default:
				if (it->second.asString().size() != 0) {
					result += it->second.asString();	
				} else {
					result += "null";
				}
		}
		if ((it != map.end()) && (next(it) != map.end())) result += ",";
	}
	result += "}";
	
	return result;
}

std::string agocontrol::variantListToJSONString(qpid::types::Variant::List list) {
	string result;
	result += "[";
	for (Variant::List::const_iterator it = list.begin(); it != list.end(); ++it) {
		switch(it->getType()) {
			case VAR_MAP:
				result += variantMapToJSONString(it->asMap());
				break;
			case VAR_LIST:
				result += variantListToJSONString(it->asList());
				break;
			case VAR_STRING:
				result += "\"" + it->asString()+ "\"";
				break;
			default:
				if (it->asString().size() != 0) {
					result += it->asString();
				} else {
					result += "null";
				}
		}
		if ((it != list.end()) && (next(it) != list.end())) result += ",";
	}
	result += "]";
	return result;
}

qpid::types::Variant::Map agocontrol::jsonToVariantMap(Json::Value value) {
	Variant::Map map;
	for (Json::ValueIterator it = value.begin(); it != value.end(); it++) {
		// printf("%s\n",it.key().asString().c_str());
		// printf("%s\n", (*it).asString().c_str());
		if ((*it).size() > 0) {
			map[it.key().asString()] = jsonToVariantMap((*it));
		} else {
			if ((*it).isString()) map[it.key().asString()] = (*it).asString();
			if ((*it).isBool()) map[it.key().asString()] = (*it).asBool();
			if ((*it).isInt()) map[it.key().asString()] = (*it).asInt();
			if ((*it).isUInt()) map[it.key().asString()] = (*it).asUInt();
			if ((*it).isDouble()) map[it.key().asString()] = (*it).asDouble();
		}
	}	
	return map;
}

qpid::types::Variant::Map agocontrol::jsonStringToVariantMap(std::string jsonstring) {
	Json::Value root;
	Json::Reader reader;
	Variant::Map result;

	if ( reader.parse(jsonstring, root)) {
		result = jsonToVariantMap(root);
	} else { 
		printf("warning, could not parse json to Variant::Map: %s\n",jsonstring.c_str());
	}
	return result;
}

// generates a uuid as string via libuuid
std::string agocontrol::generateUuid() {
	string strUuid;
	char *name;
	if ((name=(char*)malloc(38)) != NULL) {
		uuid_t tmpuuid;
		name[0]=0;
		uuid_generate(tmpuuid);
		uuid_unparse(tmpuuid,name);
		strUuid = string(name);
		free(name);
	}
	return strUuid;
}

std::string agocontrol::getConfigOption(const char *section, const char *option, const char *defaultvalue) {
	std::string result;
	t_Str value = t_Str("");
	CDataFile ExistingDF(CONFIG_FILE);

	value = ExistingDF.GetString(option, section);
	if (value.size() == 0)
		result = defaultvalue;
	else
		result = value;
	return result;
}

agocontrol::AgoConnection::AgoConnection() {
	Variant::Map connectionOptions;
	connectionOptions["username"] = getConfigOption("system", "username", "agocontrol");
	connectionOptions["password"] = getConfigOption("system", "password", "letmein");
	connectionOptions["reconnect"] = "true";

	uuidMapFile = "/tmp/test.uuidmap";
	loadUuidMap();

	connection = Connection(getConfigOption("system", "broker", "localhost:5672"),connectionOptions);
	try {
		connection.open(); 
		session = connection.createSession(); 
		receiver = session.createReceiver("agocontrol; {create: always, node: {type: topic}}");
		sender = session.createSender("agocontrol; {create: always, node: {type: topic}}"); 
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		connection.close();
		printf("could not connect to broker\n");
		_exit(1);
	}
}

agocontrol::AgoConnection::~AgoConnection() {
	try {
		connection.close();
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
	}
}


void agocontrol::AgoConnection::run() {
	reportDevices();
	while( true ) {
		try{
			Variant::Map content;
			Message message = receiver.fetch(Duration::SECOND * 3);

			// workaround for bug qpid-3445
			if (message.getContent().size() < 4) {
				throw qpid::messaging::EncodingException("message too small");
			}

			decode(message, content);
			std::cout << content << std::endl;

			session.acknowledge();
		} catch(const NoMessageAvailable& error) {
			
		} catch(const std::exception& error) {
			std::cerr << error.what() << std::endl;
		}
	}
}

bool agocontrol::AgoConnection::addDevice(const char *internalId, const char *deviceType) {
	if (internalIdToUuid(internalId).size()==0) {
		// need to generate new uuid
		uuidMap[generateUuid()] = internalId;
		storeUuidMap();
	}
	Variant::Map device;
	device["devicetype"] = deviceType;
	device["internalid"] = internalId;
	deviceMap[internalIdToUuid(internalId)] = device;
	return true;
}

std::string agocontrol::AgoConnection::uuidToInternalId(std::string uuid) {
	return uuidMap[uuid].asString();
} 

std::string agocontrol::AgoConnection::internalIdToUuid(std::string internalId) {
	string result;
	for (Variant::Map::const_iterator it = uuidMap.begin(); it != uuidMap.end(); ++it) {
		if (it->second.asString() == internalId) return it->first;
	}
	return result;
}

void agocontrol::AgoConnection::reportDevices() {
	for (Variant::Map::const_iterator it = deviceMap.begin(); it != deviceMap.end(); ++it) {
		Variant::Map device;
		Variant::Map content;
		Message event;

		// printf("uuid: %s\n", it->first.c_str());
		device = it->second.asMap();
		// printf("devicetype: %s\n", device["devicetype"].asString().c_str());
		content["devicetype"] = device["devicetype"].asString();
		content["uuid"] = it->first;
		encode(content, event);
		event.setSubject("event.device.announce");
		sender.send(event);
	}
}

bool agocontrol::AgoConnection::storeUuidMap() {
	ofstream mapfile;
	mapfile.open(uuidMapFile.c_str());
	mapfile << variantMapToJSONString(uuidMap);
	mapfile.close();
	return true;
}

bool agocontrol::AgoConnection::loadUuidMap() {
	string content;
	ifstream mapfile (uuidMapFile.c_str());
	if (mapfile.is_open()) {
		while (mapfile.good()) {
			string line;
			getline(mapfile, line);
			content += line;
		}
		mapfile.close();
	}
	uuidMap = jsonStringToVariantMap(content);
	return true;
}

