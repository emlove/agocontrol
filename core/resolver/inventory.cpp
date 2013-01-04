#include <stdio.h>
#include <unistd.h>
#include <string>

#include "inventory.h"

using namespace std;

Inventory::Inventory(const char *dbfile) {
	int rc = sqlite3_open(dbfile, &db);
	if( rc != SQLITE_OK ){
		fprintf(stderr, "Can't open database: %s\n", sqlite3_errmsg(db));
		sqlite3_close(db);
	}
}

string Inventory::getdevicename (string uuid) {
	string query = "select name from devices where uuid = '" + uuid + "'";
	return getfirst(query.c_str());
}

string Inventory::getdeviceroom (string uuid) {
	string query = "select room from devices where uuid = '" + uuid + "'";
	return getfirst(query.c_str());
}

int Inventory::setdevicename (string uuid, string name) {
	return 0;
} 

string Inventory::getroomname (string uuid) {
	string query = "select name from rooms where uuid = '" + uuid + "'";
	return getfirst(query.c_str());
}

int Inventory::setroomname (string uuid, string name) { 
	return 0;
} 

int Inventory::setdeviceroom (string deviceuuid, string roomuuid) {
	return 0;
} 

string Inventory::getdeviceroomname (string uuid) {
	string query = "select room from devices where uuid = '" + uuid + "'";
	return getroomname(getfirst(query.c_str()));
} 

Variant::Map Inventory::getrooms() {
	Variant::Map result;
	return result;
} 
int Inventory::deleteroom (string uuid) {
	return 0;
}
string Inventory::getfirst(const char *query) {
	sqlite3_stmt *stmt;
	int rc;
	string result;

	rc = sqlite3_prepare_v2(db, query, -1, &stmt, NULL);
	if(rc!=SQLITE_OK) {
		fprintf(stderr, "sql error #%d: %s\n", rc,sqlite3_errmsg(db));
		return result;
	}
	rc = sqlite3_step(stmt);
	switch(rc) {
		case SQLITE_ERROR:
			fprintf(stderr, "step error: %s\n",sqlite3_errmsg(db));
			break;
		case SQLITE_ROW:
			result =string( (const char*)sqlite3_column_text(stmt, 0));
			break;
	}
	sqlite3_finalize(stmt);
	return result;
}

/*	
int main(int argc, char **argv){
	Inventory inv("/etc/opt/agocontrol/inventory.db");
	string uuid = "41885e9b-126e-4178-9c4c-37f018bb019d";
	string room = inv.getroomname(uuid);
	printf("room: %s\n", room.c_str());

	for (int i=0;i<sqlite3_column_count(stmt);i++) {
		printf("%s = ",sqlite3_column_name(stmt, i));
		switch(sqlite3_column_type(stmt, i)) {
			case SQLITE_TEXT:
				printf("%s",sqlite3_column_text(stmt, i));
				break;
			default:
				printf("(unknown: %d)",sqlite3_column_type(stmt, i));

		}
		printf("\n");
	}
	
}
*/
