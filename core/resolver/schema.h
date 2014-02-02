
#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>


#include <fstream>
#include "yaml-cpp/yaml.h"
#include <string>

using namespace std;
using namespace qpid::messaging;
using namespace qpid::types;

qpid::types::Variant::List mergeList(qpid::types::Variant::List a, qpid::types::Variant::List b);
qpid::types::Variant::Map mergeMap(qpid::types::Variant::Map a, qpid::types::Variant::Map b);
Variant::List sequenceToVariantList(const YAML::Node &node);
Variant::Map mapToVariantMap(const YAML::Node &node);
Variant::Map parseSchema(const char *filename);

