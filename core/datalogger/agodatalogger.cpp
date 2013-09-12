#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#include <sqlite3.h>

#include "agoclient.h"

#ifndef DBFILE
#define DBFILE "/var/opt/agocontrol/datalogger.db"
#endif

using namespace std;
using namespace agocontrol;

AgoConnection *agoConnection;
sqlite3 *db;


void eventHandler(std::string subject, qpid::types::Variant::Map content) {
	sqlite3_stmt *stmt;
	int rc;
	string result;
	string uuid = content["uuid"].asString();
	string environment = subject; // todo: replacements
	string level = content["level"].asString();
	int time = 0; // todo: calc unix timestamp
	string query = "INSERT INTO data VALUES(null,?,?,?,?)";
	rc = sqlite3_prepare_v2(db, query.c_str(), -1, &stmt, NULL);
	if(rc!=SQLITE_OK) {
		fprintf(stderr, "sql error #%d: %s\n", rc,sqlite3_errmsg(db));
		return;
	}
	rc = sqlite3_step(stmt);
	switch(rc) {
		case SQLITE_ERROR:
			fprintf(stderr, "step error: %s\n",sqlite3_errmsg(db));
			break;
		case SQLITE_ROW:
			if (sqlite3_column_type(stmt, 0) == SQLITE_TEXT) result =string( (const char*)sqlite3_column_text(stmt, 0));
			break;
	}

	sqlite3_finalize(stmt);
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	if (internalid == "dataloggercontroller") {
		if (content["command"] == "getloggergraph") {
			// start, end, env, deviceid
                } else if (content["command"] == "getdevieenvironments") {


		}
	}
	return returnval;
}

int main(int argc, char **argv) {
	agoConnection = new AgoConnection("datalogger");	
	agoConnection->addDevice("dataloggercontroller", "dataloggercontroller");
	agoConnection->addHandler(commandHandler);
	agoConnection->addEventHandler(eventHandler);
	agoConnection->run();
}
