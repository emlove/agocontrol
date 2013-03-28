/*
     Copyright (C) 2013 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>
#include <sstream>
#include <string.h>

#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#include <limits.h>
#include <float.h>

#define __STDC_FORMAT_MACROS
#include <inttypes.h>

#include "agoclient.h"

#include <openzwave/Options.h>
#include <openzwave/Manager.h>
#include <openzwave/Driver.h>
#include <openzwave/Node.h>
#include <openzwave/Group.h>
#include <openzwave/Notification.h>
#include <openzwave/platform/Log.h>
#include <openzwave/value_classes/ValueStore.h>
#include <openzwave/value_classes/Value.h>
#include <openzwave/value_classes/ValueBool.h>

#include "ZWApi.h"

using namespace std;
using namespace agocontrol;
using namespace OpenZWave;

bool debug = true;

AgoConnection *agoConnection;

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

const char *controllerErrorStr (Driver::ControllerError err)
{
	switch (err) {
		case Driver::ControllerError_None:
			return "None";
		case Driver::ControllerError_ButtonNotFound:
			return "Button Not Found";
		case Driver::ControllerError_NodeNotFound:
			return "Node Not Found";
		case Driver::ControllerError_NotBridge:
			return "Not a Bridge";
		case Driver::ControllerError_NotPrimary:
			return "Not Primary Controller";
		case Driver::ControllerError_IsPrimary:
			return "Is Primary Controller";
		case Driver::ControllerError_NotSUC:
			return "Not Static Update Controller";
		case Driver::ControllerError_NotSecondary:
			return "Not Secondary Controller";
		case Driver::ControllerError_NotFound:
			return "Not Found";
		case Driver::ControllerError_Busy:
			return "Controller Busy";
		case Driver::ControllerError_Failed:
			return "Failed";
		case Driver::ControllerError_Disabled:
			return "Disabled";
		case Driver::ControllerError_Overflow:
			return "Overflow";
		default:
			return "Unknown error";
	}
}

void controller_update(Driver::ControllerState state,  Driver::ControllerError err, void *context) {
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
		case Driver::ControllerState_Cancel:
			printf("command was cancelled");
			break;
		case Driver::ControllerState_Error:
			printf("command returned error");
			break;
		case Driver::ControllerState_Sleeping:
			printf("device went to sleep");
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
	if (err != Driver::ControllerError_None)  {
		printf("%s\n", controllerErrorStr(err));
	}
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


ValueID* getValueID(int nodeid, int instance, string label) {
        for( list<NodeInfo*>::iterator it = g_nodes.begin(); it != g_nodes.end(); ++it )
        {
		for (list<ValueID>::iterator it2 = (*it)->m_values.begin(); it2 != (*it)->m_values.end(); it2++ ) {
			// printf("Node ID: %3d Value ID: %d\n", (*it)->m_nodeId, (*it2).GetId());
			if ( ((*it)->m_nodeId == nodeid) && ((*it2).GetInstance() == instance) ) {
				string valuelabel = Manager::Get()->GetValueLabel((*it2));
				if (label == valuelabel) {
					// printf("Found ValueID: %d\n",(*it2).GetId());
					return &(*it2);
				}
			}
		}
	}
	return NULL;
}

string uint64ToString(uint64_t i) {
	stringstream tmp;
	tmp << i;
	return tmp.str();
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
				stringstream tempstream;
				tempstream << (int) _notification->GetNodeId();
				tempstream << "/";
				tempstream << (int) id.GetInstance();
				string tempstring = tempstream.str();
				string label = Manager::Get()->GetValueLabel(id);
				switch(id.GetCommandClassId()) {
					case COMMAND_CLASS_SWITCH_MULTILEVEL:
						if (label == "Level") {
							printf("adding ago device dimmer for value id: %s - Label: %s\n", tempstring.c_str(),label.c_str());
							agoConnection->addDevice(tempstring.c_str(), "dimmer");
						}
					break;
					case COMMAND_CLASS_SWITCH_BINARY:
						if (label == "Switch") {
							printf("adding ago device switch for value id: %s\n", tempstring.c_str());
							agoConnection->addDevice(tempstring.c_str(), "switch");
						}
					break;
					case COMMAND_CLASS_SENSOR_BINARY:
						if (label == "Sensor") {
							printf("adding ago device binarysensor for value id: %s\n", tempstring.c_str());
							agoConnection->addDevice(tempstring.c_str(), "binarysensor");
						}
					break;
					case COMMAND_CLASS_SENSOR_MULTILEVEL:
						if (label == "Luminance") {
							printf("adding ago device multilevelsensor for value id: %s\n", tempstring.c_str());
							agoConnection->addDevice(tempstring.c_str(), "multilevelsensor");
						} else {
							printf("WARNING: unhandled label for SENSOR_MULTILEVEL: %s - adding generic multilevelsensor\n",label.c_str());
							agoConnection->addDevice(tempstring.c_str(), "multilevelsensor");
						}
					break;
					case COMMAND_CLASS_BASIC_WINDOW_COVERING:
						if (label == "Open") {
							printf("adding ago device drapes for value id: %s\n", tempstring.c_str());
							agoConnection->addDevice(tempstring.c_str(), "drapes");
						}
					break;
					case COMMAND_CLASS_THERMOSTAT_SETPOINT:
						printf("adding ago device thermostat for value id: %s\n", tempstring.c_str());
						agoConnection->addDevice(tempstring.c_str(), "thermostat");
					break;
					default:
						printf("Notification: Unassigned Value Added Home 0x%08x Node %d Genre %d Class %x Instance %d Index %d Type %d - Label: %s\n", _notification->GetHomeId(), _notification->GetNodeId(), id.GetGenre(), id.GetCommandClassId(), id.GetInstance(), id.GetIndex(), id.GetType(),label.c_str());
						// printf("Notification: Unassigned Value Added Home 0x%08x Node %d Genre %d Class %x Instance %d Index %d Type %d - ID: %" PRIu64 "\n", _notification->GetHomeId(), _notification->GetNodeId(), id.GetGenre(), id.GetCommandClassId(), id.GetInstance(), id.GetIndex(), id.GetType(),id.GetId());

				}
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

					stringstream tempstream;
					tempstream << (int) _notification->GetNodeId();
					tempstream << "/";
					tempstream << (int) id.GetInstance();

					string level = str;
					string eventtype = "";
					if (str == "True") level="255";
					if (str == "False") level="0";
					printf("Value: %s Label: %s Unit: %s\n",str.c_str(),label.c_str(),units.c_str());
					if ((label == "Basic") || (label == "Switch")) {
						eventtype="event.device.statechanged";
					}
					if (label == "Luminance") {
						eventtype="event.environment.brightnesschanged";
					}
					if (label == "Temperature") {
						eventtype="event.environment.temperaturechanged";
					}
					if (label == "Relative Humidity") {
						eventtype="event.environment.humiditychanged";
					}
					if (label == "Battery Level") {
						eventtype="event.device.batterylevelchanged";
					}
					if (label == "Alarm Level") {
						eventtype="event.security.alarmlevelchanged";
					}
					if (label == "Alarm Type") {
						eventtype="event.security.alarmtypechanged";
					}
					if (label == "Sensor") {
						eventtype="event.environment.sensortriggered";
					}
					if (label == "Energy") {
						eventtype="event.environment.energy";
					}
					if (label == "Power") {
						eventtype="event.environment.energy";
					}
					if (eventtype != "") {
						if (debug) printf("Sending %s event from child %s\n",eventtype.c_str(), tempstream.str().c_str());
						agoConnection->emitEvent(tempstream.str().c_str(), eventtype.c_str(), level.c_str(), units.c_str());	
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

			// todo: announce node
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
				ValueID id = _notification->GetValueID();

				stringstream tempstream;
				tempstream << (int) _notification->GetNodeId();
				tempstream << "/";
				tempstream << (int) id.GetInstance();
				stringstream level;
				level << _notification->GetByte();
				string eventtype = "event.device.statechanged";
				if (debug) printf("Sending %s event from child %s\n",eventtype.c_str(), tempstream.str().c_str());
				agoConnection->emitEvent(tempstream.str().c_str(), eventtype.c_str(), level.str().c_str(), "");	

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
		case Notification::Type_AllNodesQueriedSomeDead:
		{
			pthread_cond_broadcast(&initCond);
			break;
		}

		case Notification::Type_DriverReset:
		case Notification::Type_Notification:
		case Notification::Type_NodeNaming:
		case Notification::Type_NodeProtocolInfo:
		case Notification::Type_NodeQueriesComplete:
		default:
		{
		}
	}

	pthread_mutex_unlock( &g_criticalSection );
}



std::string commandHandler(qpid::types::Variant::Map content) {
	std::string internalid = content["internalid"].asString();
	// printf("command: %s internal id: %s\n", content["command"].asString().c_str(), internalid.c_str());

	if (internalid == "zwavecontroller") {
		printf("z-wave specific controller command received\n");
		if (content["command"] == "addnode") {
			Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_AddDevice, controller_update, NULL, true);
		} else if (content["command"] == "removenode") {
			Manager::Get()->BeginControllerCommand(g_homeId, Driver::ControllerCommand_RemoveDevice, controller_update, NULL, true);
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

	} else {
		unsigned pos = internalid.find("/");
		int nodeid = atoi(internalid.substr(0,pos).c_str());
		int instance = atoi(internalid.substr(pos+1).c_str());

		printf("command received for node %d/%d\n", nodeid, instance);

		if (content["command"] == "on" ) {
			ValueID *tmpValueID = getValueID(nodeid,instance, "Basic");
			if (tmpValueID) {
				// printf("Type: %s\n",Value::GetTypeNameFromEnum(tmpValueID->GetType()));
				if (debug) printf("Basic on\n");
				// printf("Found ValueID: %d\n",tmpValueID->GetId());
				bool result = Manager::Get()->SetValue(*tmpValueID , (uint8) 255);
				printf("Result: %d\n",result);
			}
			return "";
		} else if (content["command"] == "off" ) {
			ValueID *tmpValueID = getValueID(nodeid,instance, "Basic");
			if (tmpValueID) { 
				if (debug) printf("Basic off\n");
				bool result = Manager::Get()->SetValue(*tmpValueID, (uint8) 0);
				printf("Result: %d\n",result);
			}
			return "";
		} else if (content["command"] == "setlevel") {
			uint8 level = atoi(content["level"].asString().c_str());
			ValueID *tmpValueID = getValueID(nodeid,instance, "Level");
			if (tmpValueID) {
				printf("Setting level: %d\n",level);
				bool result = Manager::Get()->SetValue(*tmpValueID, level);
				printf("Result: %d\n",result);
			}
			return "";
		}
	}
	return "";
}

int main(int argc, char **argv) {
	std::string device;

	device=getConfigOption("zwave", "device", "/dev/usbzwave");


	pthread_mutexattr_t mutexattr;

	pthread_mutexattr_init ( &mutexattr );
	pthread_mutexattr_settype( &mutexattr, PTHREAD_MUTEX_RECURSIVE );

	pthread_mutex_init( &g_criticalSection, &mutexattr );
	pthread_mutexattr_destroy( &mutexattr );

	pthread_mutex_lock( &initMutex );

	
	AgoConnection _agoConnection = AgoConnection("zwave");		
	agoConnection = &_agoConnection;
	printf("connection to agocontrol established\n");

	// init open zwave
	Options::Create( "/etc/openzwave/config/", "/etc/opt/agocontrol/ozw/", "" );
	Options::Get()->AddOptionBool("PerformReturnRoutes", false );
	Options::Get()->AddOptionBool("ConsoleOutput", false ); 

	Options::Get()->Lock();
	Manager::Create();
	Manager::Get()->AddWatcher( OnNotification, NULL );
	Manager::Get()->AddDriver(device);

	// Now we just wait for the driver to become ready
	printf("waiting for OZW driver to become ready\n");
	pthread_cond_wait( &initCond, &initMutex );
	printf("pthread_cond_wait returned\n");

	if( !g_initFailed )
	{

		Manager::Get()->WriteConfig( g_homeId );
		Driver::DriverData data;
		Manager::Get()->GetDriverStatistics( g_homeId, &data );
		printf("SOF: %d ACK Waiting: %d Read Aborts: %d Bad Checksums: %d\n", data.m_SOFCnt, data.m_ACKWaiting, data.m_readAborts, data.m_badChecksum);
		printf("Reads: %d Writes: %d CAN: %d NAK: %d ACK: %d Out of Frame: %d\n", data.m_readCnt, data.m_writeCnt, data.m_CANCnt, data.m_NAKCnt, data.m_ACKCnt, data.m_OOFCnt);
		printf("Dropped: %d Retries: %d\n", data.m_dropped, data.m_retries);

		printf("agozwave startup complete, starting agoConnection->run()\n");

		agoConnection->addDevice("zwavecontroller", "zwavecontroller");
		agoConnection->addHandler(commandHandler);

		agoConnection->run();
	} else {
		printf("unable to initialize OZW\n");
	}	
	Manager::Destroy();

	pthread_mutex_destroy( &g_criticalSection );
	return 0;
}

