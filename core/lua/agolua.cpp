#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#define BOOST_FILESYSTEM_VERSION 3
#define BOOST_FILESYSTEM_NO_DEPRECATED 
#include "boost/filesystem.hpp"

#include "agoclient.h"

namespace fs = ::boost::filesystem;

using namespace std;
using namespace agocontrol;

#include "lua5.2/lua.hpp"

#ifndef LUA_SCRIPT_DIR
#define LUA_SCRIPT_DIR CONFIG_BASE_DIR "/lua/"
#endif

qpid::types::Variant::Map inventory;

AgoConnection *agoConnection;

static const luaL_Reg loadedlibs[] = {
  {"_G", luaopen_base},
  {LUA_TABLIBNAME, luaopen_table},
  {LUA_STRLIBNAME, luaopen_string},
  {LUA_MATHLIBNAME, luaopen_math},
  {NULL, NULL}
};

int luaAddDevice(lua_State *l) { // DRAFT
	int argc = lua_gettop(l);
	if (argc != 2) return 0;

	std::string internalid = lua_tostring(l, lua_gettop(l));
	lua_pop(l, 1);
	std::string devicetype = lua_tostring(l, lua_gettop(l));
	lua_pop(l, 1);

	agoConnection->addDevice(internalid.c_str(), devicetype.c_str());
	return 0;
}

int luaSendMessage(lua_State *l) {
	qpid::types::Variant::Map content;
	std::string subject;
	// number of input arguments
	int argc = lua_gettop(l);

	// print input arguments
	for(int i=0; i<argc; i++) {
		string name, value;
		if (nameval(string(lua_tostring(l, lua_gettop(l))),name, value)) {
			if (name == "subject") {
				subject = value;
			} else {
				content[name]=value;
			}
		}
		lua_pop(l, 1);
	}
	cout << "Sending message: " << subject << " " << content << endl;
	qpid::types::Variant::Map replyMap = agoConnection->sendMessageReply(subject.c_str(), content);	 
	lua_pushnumber(l, 0);
	return 1;
}

void pushTableFromMap(lua_State *L, qpid::types::Variant::Map content) {
	lua_createtable(L, 0, 0);
	for (qpid::types::Variant::Map::const_iterator it=content.begin(); it!=content.end(); it++) {
		switch (it->second.getType()) {
			case qpid::types::VAR_INT8:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asInt8());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_INT16:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asInt16());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_INT32:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asInt32());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_INT64:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asInt64());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_UINT8:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asUint8());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_UINT16:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asUint16());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_UINT32:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asUint32());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_UINT64:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asUint64());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_FLOAT:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asFloat());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_DOUBLE:
				lua_pushstring(L,it->first.c_str());
				lua_pushnumber(L,it->second.asDouble());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_STRING:
				lua_pushstring(L,it->first.c_str());
				lua_pushstring(L,it->second.asString().c_str());
				lua_settable(L, -3);
				break;
			case qpid::types::VAR_MAP:
				lua_pushstring(L,it->first.c_str());
				pushTableFromMap(L,it->second.asMap());
				lua_settable(L, -3);
				break;
			//default:
				//lua_pushstring(L,it->first.c_str());
				//lua_pushstring(L,"unhandled");
				//cout << "undhandled type: " << it->second.getType() << endl;
				//lua_settable(L, -3);
		}
	}	
}

bool runScript(qpid::types::Variant::Map content, const char *script) {
	cout << "-- running script " << script <<  endl;
	inventory = agoConnection->getInventory();
	lua_State *L;    
	const luaL_Reg *lib;

	L = luaL_newstate();
	for (lib = loadedlibs; lib->func; lib++) {
		luaL_requiref(L, lib->name, lib->func, 1);
		lua_pop(L, 1);
	}

	lua_register(L, "sendMessage", luaSendMessage);
	// lua_register(L, "addDevice", luaAddDevice);

	pushTableFromMap(L, content);
	lua_setglobal(L, "content");
	pushTableFromMap(L, inventory);
	lua_setglobal(L, "inventory");

	int status = luaL_loadfile(L, script);
	int result = 0;
	if(status == LUA_OK) {
		result = lua_pcall(L, 0, LUA_MULTRET, 0);
	} else {
		std::cout << "-- Could not load the script " << script << std::endl;
	}
	if ( result!=0 ) {
		std::cerr << "-- " << lua_tostring(L, -1) << std::endl;
		lua_pop(L, 1); // remove error message
	}

	lua_close(L);
	return status == 0 ? true : false;	
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	if (content["command"] == "inventory") return returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "luacontroller") {
		return returnval;
	} else {
		fs::path scriptdir(LUA_SCRIPT_DIR);
		if (fs::exists(scriptdir)) {
			fs::recursive_directory_iterator it(scriptdir);
			fs::recursive_directory_iterator endit;
			while (it != endit) {
				if (fs::is_regular_file(*it) && (it->path().extension().string() == ".lua") && (it->path().filename().string() != "helper.lua")) {
					runScript(content, it->path().c_str());
				}
				++it;
			}
		}
	}
	return returnval;
}

void eventHandler(std::string subject, qpid::types::Variant::Map content) {
	if (subject == "event.device.announce") return;
	content["subject"]=subject;
	commandHandler(content);
}

int main(int argc, char **argv) {

	agoConnection = new AgoConnection("lua");
	agoConnection->addDevice("luacontroller", "luacontroller");
	agoConnection->addHandler(commandHandler);
	agoConnection->addEventHandler(eventHandler);
	// sleep(5);
	// for (qpid::types::Variant::Map::const_iterator it = eventmap.begin(); it!=eventmap.end(); it++) { 


	agoConnection->run();

}
