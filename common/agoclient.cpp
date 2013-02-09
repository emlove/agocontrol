#include <string>

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

