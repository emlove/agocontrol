#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#include "agoclient.h"

using namespace std;
using namespace agocontrol;

#include "lua5.2/lua.hpp"

lua_State *L;    
static const luaL_Reg lualibs[] =
{
	{ "base", luaopen_base },
	{ NULL, NULL}
};

AgoConnection *agoConnection;

int luaSendMessage(lua_State *l) {
	cout << "called from lua" << endl;
	lua_pushnumber(l, 0);
	return 1;
}

bool runScript(qpid::types::Variant::Map content) {
	cout << "running script" << endl;
	L = luaL_newstate();
	const luaL_Reg *lib = lualibs;
	for(; lib->func != NULL; lib++) {
		lib->func(L);
		lua_settop(L, 0);
	}

	lua_register(L, "sendMessage", luaSendMessage);

	lua_createtable(L, 0, 0);
	for (qpid::types::Variant::Map::const_iterator it=content.begin(); it!=content.end(); it++) {
		lua_pushstring(L,it->first.c_str());
		switch (it->second.getType()) {
			case qpid::types::VAR_INT8:
			case qpid::types::VAR_INT16:
			case qpid::types::VAR_INT32:
			case qpid::types::VAR_INT64:
			case qpid::types::VAR_UINT8:
			case qpid::types::VAR_UINT16:
			case qpid::types::VAR_UINT32:
			case qpid::types::VAR_UINT64:
			case qpid::types::VAR_FLOAT:
			case qpid::types::VAR_DOUBLE:
				lua_pushnumber(L,it->second.asFloat());
				break;
			case qpid::types::VAR_STRING:
				lua_pushstring(L,it->second.asString().c_str());
				break;
			default:
				lua_pushstring(L,"unhandled");
		}
		lua_settable(L, -3);
	}	
	lua_setglobal(L, "content");

	int status = luaL_loadfile(L, "command.lua");
	int result = 0;
	if(status == LUA_OK) {
		result = lua_pcall(L, 0, LUA_MULTRET, 0);
	} else {
		std::cout << " Could not load the script." << std::endl;
	}
	if ( status!=0 ) {
		std::cerr << "-- " << lua_tostring(L, -1) << std::endl;
		lua_pop(L, 1); // remove error message
	}

	lua_close(L);
	return status == 0 ? true : false;	
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "luacontroller") {
		return returnval;
	} else {

	}
	return returnval;
}

void eventHandler(std::string subject, qpid::types::Variant::Map content) {
	content["subject"]=subject;
	runScript(content);
}

int main(int argc, char **argv) {

	agoConnection = new AgoConnection("lua");
	agoConnection->addDevice("luacontroller", "luacontroller");
	agoConnection->addHandler(commandHandler);
	agoConnection->setFilter(false);
	agoConnection->addEventHandler(eventHandler);

	agoConnection->run();

}
