#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <pthread.h>

#include <string>
#include <iostream>
#include <sstream>
#include <cerrno>

#include <sqlite3.h>

#include <boost/date_time/posix_time/time_parsers.hpp>
#include <boost/date_time/posix_time/posix_time_types.hpp>


#include "agoclient.h"

#ifndef DBFILE
#define DBFILE "/var/opt/agocontrol/datalogger.db"
#endif

using namespace std;
using namespace agocontrol;

AgoConnection *agoConnection;
sqlite3 *db;
qpid::types::Variant::Map inventory;

std::string uuidToName(std::string uuid) {
	qpid::types::Variant::Map devices = inventory["inventory"].asMap();
	qpid::types::Variant::Map device = devices[uuid].asMap();
	return device["name"].asString() == "" ? uuid : device["name"].asString();
}

void eventHandler(std::string subject, qpid::types::Variant::Map content) {
	sqlite3_stmt *stmt;
	int rc;
	string result;
	string uuid = uuidToName(content["uuid"].asString());
	cout << subject << " " << content << endl;
	if (subject != "" && content["level"].asString() != "") {
		string environment = subject;
		replaceString(subject, "event.environment.", "");
		replaceString(subject, "changed", "");
		replaceString(subject, "event,", "");
		cout << "environment: " << environment << endl;
		string level = content["level"].asString();

		string query = "INSERT INTO data VALUES(null, ?, ?, ?, ?)";
		rc = sqlite3_prepare_v2(db, query.c_str(), -1, &stmt, NULL);
		if(rc!=SQLITE_OK) {
			fprintf(stderr, "sql error #%d: %s\n", rc,sqlite3_errmsg(db));
			return;
		}
		
		sqlite3_bind_text(stmt, 1, uuid.c_str(), -1, NULL);
		sqlite3_bind_text(stmt, 2, environment.c_str(), -1, NULL);
		sqlite3_bind_text(stmt, 3, level.c_str(), -1, NULL);
		sqlite3_bind_int(stmt, 4, time(NULL));
		
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
}

void GetGraphData(qpid::types::Variant::Map content, qpid::types::Variant::Map &result) {
    printf("start is: %s\n", content["start"].asString().c_str());
    boost::posix_time::ptime base(boost::gregorian::date(1970, 1, 1));
    boost::posix_time::time_duration start = boost::posix_time::time_from_string(content["start"].asString()) - base;
    printf("%d\n", start.total_seconds());
    
    
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	printf("WTF!!!"); // FIXME: Never gets called?!?
	std::cout <<  content["internalid"].asString() << std::endl;
	if (internalid == "dataloggercontroller") {
		if (content["command"] == "getloggergraph") {
		    GetGraphData(content, returnval);
			// start, end, env, deviceid
        } else if (content["command"] == "getdevieenvironments") {


		}
	}
	return returnval;
}

int main(int argc, char **argv) {
    int rc = sqlite3_open(DBFILE, &db);
	if( rc != SQLITE_OK ){
		fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
		sqlite3_close(db);
		return 1;
	}
	agoConnection = new AgoConnection("datalogger");	
	agoConnection->addDevice("dataloggercontroller", "dataloggercontroller");
	agoConnection->addHandler(commandHandler);
	agoConnection->addEventHandler(eventHandler);
	inventory = agoConnection->getInventory();
	agoConnection->run();

	return 0;
}
