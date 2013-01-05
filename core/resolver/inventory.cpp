#include <stdio.h>
#include <unistd.h>
#include <iostream>
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
        if (getdevicename(uuid) == "") { // does not exist, create
                string query = "insert into devices (name, uuid) VALUES ('" + name + "','" + uuid + "')";
                printf("creating device: %s\n", query.c_str());
                getfirst(query.c_str());
        } else {
                string query = "update devices set name = '" + name + "' where uuid = '" + uuid + "'";
                getfirst(query.c_str());
        }
        if (getdevicename(uuid) == name) {
                return 0;
        } else {
                return 1;
        }
} 

string Inventory::getroomname (string uuid) {
	string query = "select name from rooms where uuid = '" + uuid + "'";
	return getfirst(query.c_str());
}

int Inventory::setroomname (string uuid, string name) { 
	if (getroomname(uuid) == "") { // does not exist, create
		string query = "insert into rooms (name, uuid) VALUES ('" + name + "','" + uuid + "')";
		printf("creating room: %s\n", query.c_str());
		getfirst(query.c_str());
	} else {
		string query = "update rooms set name = '" + name + "' where uuid = '" + uuid + "'";
		getfirst(query.c_str());
	}
	if (getroomname(uuid) == name) {
		return 0;
	} else {
		return 1;
	}
} 

int Inventory::setdeviceroom (string deviceuuid, string roomuuid) {
	string query = "update devices set room = '" + roomuuid + "' where uuid = '" + deviceuuid + "'";
	getfirst(query.c_str());
	if (getdeviceroom(deviceuuid) == roomuuid) {
		return 0;
	} else {
		return 1;
	}
} 

string Inventory::getdeviceroomname (string uuid) {
	string query = "select room from devices where uuid = '" + uuid + "'";
	return getroomname(getfirst(query.c_str()));
} 

Variant::Map Inventory::getrooms() {
	Variant::Map result;
	sqlite3_stmt *stmt;
	int rc;

	rc = sqlite3_prepare_v2(db, "select uuid, name, location from rooms", -1, &stmt, NULL);
	if(rc!=SQLITE_OK) {
                fprintf(stderr, "sql error #%d: %s\n", rc,sqlite3_errmsg(db));
                return result;
        }
        while (sqlite3_step(stmt) == SQLITE_ROW) {
		Variant::Map entry;
		const char *roomname = (const char*)sqlite3_column_text(stmt, 1);
		const char *location = (const char*)sqlite3_column_text(stmt, 2);
		const char *uuid = (const char*)sqlite3_column_text(stmt, 0);
		if (roomname != NULL) {
			entry["name"] = string(roomname);
		} else {
			entry["name"] = "";
		} 
		if (location != NULL) {
			entry["location"] = string(location);
		} else {	
			entry["location"] = "";
		}
		if (uuid != NULL) {
			result[uuid] = entry;
		}
	}
	return result;
} 
int Inventory::deleteroom (string uuid) {
	string query = "update devices set room = '' where uuid = '" + uuid + "'";
	getfirst(query.c_str());
	query = "delete from rooms where uuid = '" + uuid + "'";
	getfirst(query.c_str());
	if (getroomname(uuid) == "") {
		return 0;
	} else {
		return 1;
	}
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
	cout << inv.setdevicename("1234", "1235") << endl;
	cout << inv.deleteroom("1234") << endl;
	cout << inv.getdevicename("1234");
	cout << inv.getrooms();
}
*/
