#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include <string>

#include <sqlite3.h>

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

class Inventory {
	public:
		Inventory(const char *dbfile);
		string getdevicename (string uuid);
		string getdeviceroom (string uuid);
		int setdevicename (string uuid, string name);
		string getroomname (string uuid);
		int setroomname (string uuid, string name);
		int setdeviceroom (string deviceuuid, string roomuuid);
		string getdeviceroomname (string uuid);
		Variant::Map getrooms();
		int deleteroom (string uuid);
	private:
		sqlite3 *db;
		string getfirst(const char *query);
};
