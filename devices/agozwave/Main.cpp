//
//	AMQP wrapper for OpenZWave.
//
//	Copyright (c) 2010 Mal Lansell <mal@openzwave.com>
//	Copyright (c) 2012 Harald Klein <hari@vt100.at>
//
//	SOFTWARE NOTICE AND LICENSE
//
//	This code is derived from the OpenZWave example MiniOZW/Main.cpp
//
//	This is free software: you can redistribute it and/or modify
//	it under the terms of the GNU Lesser General Public License as published
//	by the Free Software Foundation, either version 3 of the License,
//	or (at your option) any later version.
//
//	You should have received a copy of the GNU Lesser General Public License
//	along with this code.  If not, see <http://www.gnu.org/licenses/>.
//

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>
#include <openzwave/Options.h>
#include <openzwave/Manager.h>
#include <openzwave/Driver.h>
#include <openzwave/Node.h>
#include <openzwave/Group.h>
#include <openzwave/Notification.h>
#include <openzwave/value_classes/ValueStore.h>
#include <openzwave/value_classes/Value.h>
#include <openzwave/value_classes/ValueBool.h>

#include "ZWApi.h"

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Receiver.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>
#include <qpid/messaging/Address.h>

#include <uuid/uuid.h>
#include <stdlib.h>

#include <iostream>

#include <limits.h>
#include <float.h>

#include "CDataFile.h"


using namespace qpid::messaging;
using namespace qpid::types;
using namespace OpenZWave;


Sender sender;

static uint32 g_homeId = 0;
static bool   g_initFailed = false;

typedef struct
{
	uint32			m_homeId;
	uint8			m_nodeId;
	bool			m_polled;
	list<ValueID>	m_values;
}NodeInfo;

static list<NodeInfo*> g_nodes;
static pthread_mutex_t g_criticalSection;
static pthread_cond_t  initCond  = PTHREAD_COND_INITIALIZER;
static pthread_mutex_t initMutex = PTHREAD_MUTEX_INITIALIZER;

void sendStatusUpdate(string uuid, string level);
void sendBrightnessChangedEvent(string uuid, string level, string unit);
void sendTemperatureChangedEvent(string uuid, string level, string unit);
void sendHumidityChangedEvent(string uuid, string level, string unit);
void sendBatteryLevelChangedEvent(string uuid, string level, string unit);
void sendAlarmLevelChangedEvent(string uuid, string level, string unit);
void sendAlarmTypeChangedEvent(string uuid, string level, string unit);
void sendSensorChangedEvent(string uuid, string level, string unit);
void sendPowerChangedEvent(string uuid, string level, string unit);
void sendEnergyChangedEvent(string uuid, string level, string unit);


void controller_update(Driver::ControllerState state, void *context) {
	printf("controller state update:");
	switch(state) {
		case Driver::ControllerState_Normal:
			printf("no command in progress");
			// nothing to do
			break;
		case Driver::ControllerState_Waiting:
			printf("waiting for user action");
			// waiting for user action
			break;
		case Driver::ControllerState_InProgress:
			printf("communicating with other device");
			// communicating with device
			break;
		case Driver::ControllerState_Completed:
			printf("command has completed successfully");
			break;
		case Driver::ControllerState_Failed:
			printf("command has failed");
			// houston..
			break;
		case Driver::ControllerState_NodeOK:
			printf("node ok");
			break;
		case Driver::ControllerState_NodeFailed:
			printf("node failed");
			break;
		default:
			printf("unknown response");
			break;
	}
	printf("\n");
}

//-----------------------------------------------------------------------------
// <GetNodeInfo>
// Callback that is triggered when a value, group or node changes
//-----------------------------------------------------------------------------
NodeInfo* GetNodeInfo
(
	Notification const* _notification
)
{
	uint32 const homeId = _notification->GetHomeId();
	uint8 const nodeId = _notification->GetNodeId();
	for( list<NodeInfo*>::iterator it = g_nodes.begin(); it != g_nodes.end(); ++it )
	{
		NodeInfo* nodeInfo = *it;
		if( ( nodeInfo->m_homeId == homeId ) && ( nodeInfo->m_nodeId == nodeId ) )
		{
			return nodeInfo;
		}
	}

	return NULL;
}

//-----------------------------------------------------------------------------
// <OnNotification>
// Callback that is triggered when a value, group or node changes
//-----------------------------------------------------------------------------
void OnNotification
(
	Notification const* _notification,
	void* _context
)
{
	// Must do this inside a critical section to avoid conflicts with the main thread
	pthread_mutex_lock( &g_criticalSection );

	switch( _notification->GetType() )
	{
		case Notification::Type_ValueAdded:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				// Add the new value to our list
				nodeInfo->m_values.push_back( _notification->GetValueID() );
				ValueID id = _notification->GetValueID();
				printf("Notification: Value Added Home 0x%08x Node %d Genre %d Class %d Instance %d Index %d Type %d\n", _notification->GetHomeId(), _notification->GetNodeId(), id.GetGenre(), id.GetCommandClassId(), id.GetInstance(), id.GetIndex(), id.GetType());
			}
			break;
		}

		case Notification::Type_ValueRemoved:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				// Remove the value from out list
				for( list<ValueID>::iterator it = nodeInfo->m_values.begin(); it != nodeInfo->m_values.end(); ++it )
				{
					if( (*it) == _notification->GetValueID() )
					{
						nodeInfo->m_values.erase( it );
						break;
					}
				}
			}
			break;
		}

		case Notification::Type_ValueChanged:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				// One of the node values has changed
				// TBD...
				// nodeInfo = nodeInfo;
				ValueID id = _notification->GetValueID();
				string str;
				printf("Notification: Value Changed Home 0x%08x Node %d Genre %d Class %d Instance %d Index %d Type %d\n", _notification->GetHomeId(), _notification->GetNodeId(), id.GetGenre(), id.GetCommandClassId(), id.GetInstance(), id.GetIndex(), id.GetType());
			      if (Manager::Get()->GetValueAsString(id, &str)) {
					string label = Manager::Get()->GetValueLabel(id);
					string units = Manager::Get()->GetValueUnits(id);
					string level = str;
					if (str == "True") level="255";
					if (str == "False") level="0";
					printf("Value: %s Label: %s Unit: %s\n",str.c_str(),label.c_str(),units.c_str());
					string uuidstr = Manager::Get()->GetNodeName(nodeInfo->m_homeId,nodeInfo->m_nodeId);
					if (label == "Basic") {
						sendStatusUpdate( uuidstr , level);
					}
					if (label == "Luminance") {
						sendBrightnessChangedEvent(uuidstr, level, units);
					}
					if (label == "Temperature") {
						sendTemperatureChangedEvent(uuidstr, level, units);
					}
					if (label == "Relative Humidity") {
						sendHumidityChangedEvent(uuidstr, level, units);
					}
					if (label == "Battery Level") {
						sendBatteryLevelChangedEvent(uuidstr, level, units);
					}
					if (label == "Alarm Level") {
						sendAlarmLevelChangedEvent(uuidstr, level, units);
					}
					if (label == "Alarm Type") {
						sendAlarmTypeChangedEvent(uuidstr, level, units);
					}
					if (label == "Sensor") {
						sendSensorChangedEvent(uuidstr, level, units);
					}
					if (label == "Energy") {
						sendEnergyChangedEvent(uuidstr, level, units);
					}
					if (label == "Power") {
						sendPowerChangedEvent(uuidstr, level, units);
					}
						
				}
			}
			break;
		}

		case Notification::Type_Group:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				// One of the node's association groups has changed
				// TBD...
				nodeInfo = nodeInfo;
			}
			break;
		}

		case Notification::Type_NodeAdded:
		{
			// Add the new node to our list
			NodeInfo* nodeInfo = new NodeInfo();
			nodeInfo->m_homeId = _notification->GetHomeId();
			nodeInfo->m_nodeId = _notification->GetNodeId();
			nodeInfo->m_polled = false;		
			g_nodes.push_back( nodeInfo );

			uuid_t uuid;

			// check if the device already has an uuid, generate and store one if not
			if(uuid_parse(Manager::Get()->GetNodeName(_notification->GetHomeId(), _notification->GetNodeId()).c_str(), uuid) == -1) {
				char *name;

				if ((name=(char*)malloc(1024)) != NULL) {
					name[0]=0;
					uuid_generate(uuid);
					uuid_unparse(uuid,name);
					Manager::Get()->SetNodeName(_notification->GetHomeId(), _notification->GetNodeId(),name);
					free(name);
				}
			}
			break;
		}

		case Notification::Type_NodeRemoved:
		{
			// Remove the node from our list
			uint32 const homeId = _notification->GetHomeId();
			uint8 const nodeId = _notification->GetNodeId();
			for( list<NodeInfo*>::iterator it = g_nodes.begin(); it != g_nodes.end(); ++it )
			{
				NodeInfo* nodeInfo = *it;
				if( ( nodeInfo->m_homeId == homeId ) && ( nodeInfo->m_nodeId == nodeId ) )
				{
					g_nodes.erase( it );
					break;
				}
			}
			break;
		}

		case Notification::Type_NodeEvent:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				// We have received an event from the node, caused by a
				// basic_set or hail message.
				// TBD...

				Variant::Map content;
				Message event;

				nodeInfo = nodeInfo;

				try {
					content["uuid"] = Manager::Get()->GetNodeName(_notification->GetHomeId(), _notification->GetNodeId());
					content["level"] = _notification->GetByte();
					encode(content, event);
					event.setSubject("event.device.statechanged");
					sender.send(event);
				} catch(const std::exception& error) {
					std::cout << error.what() << std::endl;
				}

			}
			break;
		}

		case Notification::Type_PollingDisabled:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				nodeInfo->m_polled = false;
			}
			break;
		}

		case Notification::Type_PollingEnabled:
		{
			if( NodeInfo* nodeInfo = GetNodeInfo( _notification ) )
			{
				nodeInfo->m_polled = true;
			}
			break;
		}

		case Notification::Type_DriverReady:
		{
			g_homeId = _notification->GetHomeId();
			break;
		}


		case Notification::Type_DriverFailed:
		{
			g_initFailed = true;
			pthread_cond_broadcast(&initCond);
			break;
		}

		case Notification::Type_AwakeNodesQueried:
		case Notification::Type_AllNodesQueried:
		{
				pthread_cond_broadcast(&initCond);
				break;
		}

		default:
		{
		}
	}

	pthread_mutex_unlock( &g_criticalSection );
}

void sendStatusUpdate(string uuid, string level) {
	Variant::Map content;
	Message event;
	try {
		content["uuid"] = uuid;
		content["level"] = level;
		encode(content, event);
		event.setSubject("event.device.statechanged");
		sender.send(event);
	} catch(const std::exception& error) {
		std::cout << error.what() << std::endl;
	}

}
void sendEvent(string uuid, string level, string unit, string event) {
	Variant::Map content;
	Message myevent;
	try {
		content["uuid"] = uuid;
		content["level"] = level;
		content["unit"] = unit;
		encode(content, myevent);
		myevent.setSubject(event);
		sender.send(myevent);
	} catch(const std::exception& error) {
		std::cout << error.what() << std::endl;
	}
}

void sendBrightnessChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.environment.brightnesschanged");
}
void sendTemperatureChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.environment.temperaturechanged");
}
void sendHumidityChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.environment.humiditychanged");
}
void sendBatteryLevelChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.device.batterylevelchanged");
}
void sendAlarmLevelChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.security.alarmlevelchanged");
}
void sendAlarmTypeChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.security.alarmtypechanged");
}
void sendSensorChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.environment.sensorchanged");
}
void sendPowerChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.environment.power");
}
void sendEnergyChangedEvent(string uuid, string level, string unit) {
	sendEvent(uuid, level, unit, "event.environment.energy");
}

void reportDevices() {

	for( list<NodeInfo*>::iterator it = g_nodes.begin(); it != g_nodes.end(); ++it )
	{
		NodeInfo* nodeInfo = *it;
		Variant::Map content;
		Message event;
		try {
			content["uuid"] = Manager::Get()->GetNodeName(nodeInfo->m_homeId,nodeInfo->m_nodeId);
			content["product"] = Manager::Get()->GetNodeProductName(nodeInfo->m_homeId,nodeInfo->m_nodeId);
			content["manufacturer"] = Manager::Get()->GetNodeManufacturerName(nodeInfo->m_homeId,nodeInfo->m_nodeId);
			content["internal-id"] = nodeInfo->m_nodeId;
			switch (Manager::Get()->GetNodeGeneric(nodeInfo->m_homeId,nodeInfo->m_nodeId)) {
				case GENERIC_TYPE_GENERIC_CONTROLLER:
				case GENERIC_TYPE_STATIC_CONTROLLER:
				case GENERIC_TYPE_SWITCH_REMOTE:
					content["devicetype"]="controller";
					break;
				case GENERIC_TYPE_THERMOSTAT:
					content["devicetype"]="thermostat";
					break;
				case GENERIC_TYPE_SWITCH_MULTILEVEL:
					switch (Manager::Get()->GetNodeGeneric(nodeInfo->m_homeId,nodeInfo->m_nodeId)) {
						case SPECIFIC_TYPE_MOTOR_MULTIPOSITION:
						case SPECIFIC_TYPE_CLASS_A_MOTOR_CONTROL:
						case SPECIFIC_TYPE_CLASS_B_MOTOR_CONTROL:
						case SPECIFIC_TYPE_CLASS_C_MOTOR_CONTROL:
							content["devicetype"]="drapes";
							break;
						case SPECIFIC_TYPE_NOT_USED:
						case SPECIFIC_TYPE_POWER_SWITCH_MULTILEVEL:
						case SPECIFIC_TYPE_SCENE_SWITCH_MULTILEVEL:
						default:
							content["devicetype"]="dimmer";
							break;
					
					}
					break;
				case GENERIC_TYPE_SWITCH_BINARY:
					content["devicetype"]="switch";
					break;
				case GENERIC_TYPE_SENSOR_BINARY:
					content["devicetype"]="binarysensor";
					break;
				case GENERIC_TYPE_WINDOW_COVERING:
					content["devicetype"]="drapes";
					break;
				case GENERIC_TYPE_SENSOR_MULTILEVEL:
					content["devicetype"]="multilevelsensor";
					break;
				case GENERIC_TYPE_SENSOR_ALARM:
					switch (Manager::Get()->GetNodeSpecific(nodeInfo->m_homeId,nodeInfo->m_nodeId)) {
						case SPECIFIC_TYPE_BASIC_ROUTING_SMOKE_SENSOR:
						case SPECIFIC_TYPE_ROUTING_SMOKE_SENSOR:
						case SPECIFIC_TYPE_BASIC_ZENSOR_NET_SMOKE_SENSOR:
						case SPECIFIC_TYPE_ZENSOR_NET_SMOKE_SENSOR:
						case SPECIFIC_TYPE_ADV_ZENSOR_NET_SMOKE_SENSOR:
							content["devicetype"]="smokedetector";
							break;
					}
					break;
				default:
					break;
			}
	 		if (nodeInfo->m_nodeId==Manager::Get()->GetControllerNodeId(nodeInfo->m_homeId)) {
				// this is the controller we're talking to with ozw, announce it as special device for z-wave management
				content["devicetype"]="zwavecontroller";
			}
			encode(content, event);
			event.setSubject("event.device.announce");
			sender.send(event);
		} catch(const std::exception& error) {
			std::cout << error.what() << std::endl;
		}
	}
}

//-----------------------------------------------------------------------------
// <main>
// Create the driver and then wait
//-----------------------------------------------------------------------------
int main( int argc, char* argv[] )
{
	std::string broker;
	std::string devicefile;

	Variant::Map connectionOptions;

	// parse config
	CDataFile ExistingDF("/etc/opt/agocontrol/config.ini");

	t_Str szBroker  = t_Str("");
	szBroker = ExistingDF.GetString("broker", "system");
	if ( szBroker.size() == 0 )
		broker="localhost:5672";
	else		
		broker= szBroker;

	t_Str szDevice = t_Str("");
	szDevice = ExistingDF.GetString("device", "zwave");
	if ( szDevice.size() == 0 )
		devicefile="/dev/ttyUSB0";
	else		
		devicefile= szDevice;

	t_Str szUsername  = t_Str("");
	szUsername = ExistingDF.GetString("username", "system");
	if ( szUsername.size() == 0 )
		connectionOptions["username"]="agocontrol";
	else		
		connectionOptions["username"] = szUsername;

	t_Str szPassword  = t_Str("");
	szPassword = ExistingDF.GetString("password", "system");
	if ( szPassword.size() == 0 )
		connectionOptions["password"]="letmein";
	else		
		connectionOptions["password"]=szPassword;

	connectionOptions["reconnect"] = "true";

	Receiver receiver;
	Session session;
	Connection connection(broker, connectionOptions);
	try {
		connection.open(); 
		session = connection.createSession(); 
		receiver = session.createReceiver("agocontrol; {create: always, node: {type: topic}}"); 
		sender = session.createSender("agocontrol; {create: always, node: {type: topic}}"); 
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		connection.close();
		printf("could not startup\n");
		return 1;
	}

	pthread_mutexattr_t mutexattr;

	pthread_mutexattr_init ( &mutexattr );
	pthread_mutexattr_settype( &mutexattr, PTHREAD_MUTEX_RECURSIVE );

	pthread_mutex_init( &g_criticalSection, &mutexattr );
	pthread_mutexattr_destroy( &mutexattr );

	pthread_mutex_lock( &initMutex );

	// Create the OpenZWave Manager.
	// The first argument is the path to the config files (where the manufacturer_specific.xml file is located
	// The second argument is the path for saved Z-Wave network state and the log file.  If you leave it NULL 
	// the log file will appear in the program's working directory.
	Options::Create( "/etc/openzwave/config/", "/etc/opt/agocontrol/ozw/", "" );
	Options::Get()->Lock();

	Manager::Create();

	Manager::Get()->AddWatcher( OnNotification, NULL );

	Manager::Get()->AddDriver(devicefile );

	// Now we just wait for the driver to become ready
	pthread_cond_wait( &initCond, &initMutex );

	if( !g_initFailed )
	{

		Manager::Get()->WriteConfig( g_homeId );

		Driver::DriverData data;
		Manager::Get()->GetDriverStatistics( g_homeId, &data );
		// printf("SOF: %d ACK Waiting: %d Read Aborts: %d Bad Checksums: %d\n", data.s_SOFCnt, data.s_ACKWaiting, data.s_readAborts, data.s_badChecksum);
		// printf("Reads: %d Writes: %d CAN: %d NAK: %d ACK: %d Out of Frame: %d\n", data.s_readCnt, data.s_writeCnt, data.s_CANCnt, data.s_NAKCnt, data.s_ACKCnt, data.s_OOFCnt);
		// printf("Dropped: %d Retries: %d\n", data.s_dropped, data.s_retries);

		reportDevices();
	 	int ourNodeId = Manager::Get()->GetControllerNodeId(g_homeId);

		while( true )
		{

			// Do stuff
			try{
				Variant::Map content;
				int node = 0;
				Message message = receiver.fetch(Duration::SECOND * 3);

				// workaround for bug qpid-3445
				if (message.getContent().size() < 4) {
					throw qpid::messaging::EncodingException("message too small");
				}

				decode(message, content);
				// std::cout << content << std::endl;

				// try to map the uuid to a zwave node
				for( list<NodeInfo*>::iterator it = g_nodes.begin(); it != g_nodes.end(); ++it )
				{
					NodeInfo* nodeInfo = *it;
					if (Manager::Get()->GetNodeName(nodeInfo->m_homeId,nodeInfo->m_nodeId) == content["uuid"]) {
						string uuid = content["uuid"];
						node = nodeInfo->m_nodeId;
							
						// printf("found z-wave node id %d for uuid %s\n",node, uuid.c_str());
						break;
					}
				}
				// check if this is for a zwave node (otherwise we would not be able to resolve the uuid so node would equal to 0)
				// it should also not be our node id because then we want to branch into the controller commands
				if (node != 0 && node != ourNodeId) {

					if (content["command"] == "on") {
						printf("sending on to node %d\n", node);
						pthread_mutex_lock( &g_criticalSection );
						Manager::Get()->SetNodeOn(g_homeId,node);
						pthread_mutex_unlock( &g_criticalSection );
					} else if (content["command"] == "setlevel") {
						int level = 0;
						level = content["level"];
						pthread_mutex_lock( &g_criticalSection );
						Manager::Get()->SetNodeLevel(g_homeId,node,level);
						pthread_mutex_unlock( &g_criticalSection );
					} else if (content["command"] == "off") {
						printf("sending off to node %d\n", node);
						pthread_mutex_lock( &g_criticalSection );
						Manager::Get()->SetNodeOff(g_homeId,node);
						pthread_mutex_unlock( &g_criticalSection );
					}

					const Address& replyaddress = message.getReplyTo();
					if (replyaddress) {
						Sender replysender = session.createSender(replyaddress);
						Message response("ACK");
						replysender.send(response);
					} 
				} else {
					// this command lacks an uuid so is probably for the z-wave device itself, check for special commands here
					if (content["command"] == "discover") {
						reportDevices();
					}
					// this command has a uuid but was not for one of the childs, check if it is for the amqpOZW device itself (well known uuid)
					if (node == ourNodeId) {
						printf("z-wave specific controller command received\n");
						if (content["command"] == "addnode") {
							Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_AddDevice, controller_update, NULL, true);
						} else if (content["command"] == "removenode") {
							Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_RemoveDevice, controller_update, NULL, true);
						} else if (content["command"] == "addcontroller") {
							Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_AddController, controller_update, NULL, true);
						} else if (content["command"] == "removecontroller") {
							Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_RemoveController, controller_update, NULL, true);
						} else if (content["command"] == "addassociation") {
							int mynode = content["node"];
							int mygroup = content["group"];
							int mytarget = content["target"];
							printf("adding association: %i %i %i\n",mynode,mygroup,mytarget);
							Manager::Get()->AddAssociation(g_homeId, mynode, mygroup, mytarget);
						} else if (content["command"] == "removeassociation") {
							Manager::Get()->RemoveAssociation(g_homeId, content["node"], content["group"], content["target"]);
						} else if (content["command"] == "setconfigparam") {
							int mynode = content["node"];
							int myparam = content["param"];
							int myvalue = content["value"];
							int mysize = content["size"];
							printf("setting config param: node: %i param: %i size: %i value: %i\n",mynode,myparam,mysize,myvalue);
							Manager::Get()->SetConfigParam(g_homeId,mynode,myparam,myvalue,mysize); 
						} else if (content["command"] == "downloadconfig") {
							Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_ReceiveConfiguration, controller_update, NULL, true);
						} else if (content["command"] == "cancel") {
							Manager::Get()->CancelControllerCommand(g_homeId);
						} else if (content["command"] == "saveconfig") {
							Manager::Get()->WriteConfig( g_homeId );
						} else if (content["command"] == "allon") {
							Manager::Get()->SwitchAllOn(g_homeId );
						} else if (content["command"] == "alloff") {
							Manager::Get()->SwitchAllOff(g_homeId );
						} else if (content["command"] == "reset") {
							Manager::Get()->ResetController(g_homeId);
						}
					}
				}
						

				session.acknowledge();
			} catch(const NoMessageAvailable& error) {
				
			} catch(const std::exception& error) {
				std::cerr << error.what() << std::endl;
			}

		}
	}

	try {
		connection.close();
	} catch(const std::exception& error) {
		std::cerr << error.what() << std::endl;
		connection.close();
		return 1;
	}

	Manager::Destroy();

	pthread_mutex_destroy( &g_criticalSection );
	return 0;
}
