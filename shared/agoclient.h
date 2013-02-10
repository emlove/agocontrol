#include <string>

#include <malloc.h>
#include <stdio.h>
#include <unistd.h>

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include <jsoncpp/json/value.h>

#include <uuid/uuid.h>

#include "CDataFile.h"

#define CONFIG_FILE "/etc/opt/agocontrol/config.ini"

namespace agocontrol {

	// these will convert back and forth between a Variant type and JSON
	std::string variantMapToJSONString(qpid::types::Variant::Map map);
	std::string variantListToJSONString(qpid::types::Variant::List list);
	qpid::types::Variant::Map jsonToVariantMap(Json::Value value);
	qpid::types::Variant::Map jsonStringToVariantMap(std::string jsonstring);

	// helper to generate a string containing a uuid
	std::string generateUuid();

	// fetch a value from the config file
	std::string getConfigOption(const char *section, const char *option, const char *defaultvalue);

	// connection class
	class AgoConnection {
		protected:
			qpid::messaging::Connection connection;
			qpid::messaging::Sender sender;
			qpid::messaging::Receiver receiver;
			qpid::messaging::Session session;
			qpid::types::Variant::Map deviceMap; // this holds the internal device list
			qpid::types::Variant::Map uuidMap; // this holds the permanent uuid to internal id mapping
			bool storeUuidMap(); // stores the map on disk
			bool loadUuidMap(); // loads it
			string uuidMapFile;
			std::string uuidToInternalId(std::string uuid); // lookup in map
			std::string internalIdToUuid(std::string internalId); // lookup in map
			void reportDevices();
			std::string (*commandHandler)(qpid::types::Variant::Map);
		public:
			AgoConnection();
			~AgoConnection();
			void run();
			bool addDevice(const char *internalId, const char *deviceType);
			bool addHandler(std::string (*handler)(qpid::types::Variant::Map));
			bool sendMessage(const char *subject, qpid::types::Variant::Map content);
			bool sendMessage(qpid::types::Variant::Map content);
	};
}


