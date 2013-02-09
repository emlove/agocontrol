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

namespace agocontrol {

	std::string variantMapToJSONString(qpid::types::Variant::Map map);
	std::string variantListToJSONString(qpid::types::Variant::List list);
	qpid::types::Variant::Map jsonToVariantMap(Json::Value value);
	qpid::types::Variant::Map jsonStringToVariantMap(std::string jsonstring);
	std::string generateUuid();

}


