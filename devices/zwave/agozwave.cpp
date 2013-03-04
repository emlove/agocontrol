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


ValueID* getValueID(string id) {
	uint64_t tmpid;
	tmpid=atoll(id.c_str());

        for( list<NodeInfo*>::iterator it = g_nodes.begin(); it != g_nodes.end(); ++it )
        {
		for (list<ValueID>::iterator it2 = (*it)->m_values.begin(); it2 != (*it)->m_values.end(); it2++ ) {
			// printf("Node ID: %3d Value ID: %d\n", (*it)->m_nodeId, (*it2).GetId());
			if ((*it2).GetId() == tmpid) return &(*it2);
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
				printf("Notification: Value Added Home 0x%08x Node %d Genre %d Class %d Instance %d Index %d Type %d - ID: %" PRIu64 "\n", _notification->GetHomeId(), _notification->GetNodeId(), id.GetGenre(), id.GetCommandClassId(), id.GetInstance(), id.GetIndex(), id.GetType(),id.GetId());
				string tempstring;
				tempstring = uint64ToString(id.GetId());
				if (id.GetCommandClassId() == 0x25) {
					printf("adding ago device switch for value id: %s\n", tempstring.c_str());
					agoConnection->addDevice(tempstring.c_str(), "switch");
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
					string level = str;
					if (str == "True") level="255";
					if (str == "False") level="0";
					printf("Value: %s Label: %s Unit: %s\n",str.c_str(),label.c_str(),units.c_str());
						
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
				// TBD...
				// TODO: send level changed on basic set
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



std::string commandHandler(qpid::types::Variant::Map content) {
	std::string internalid = content["internalid"].asString();
	printf("command: %s internal id: %s\n", content["command"].asString().c_str(), internalid.c_str());
	ValueID *tmpValueID = getValueID(internalid);
	if (tmpValueID == NULL) {
		printf("can't resolve ValueID\n");
		return "";
	} else {
		printf("command received for node id %i\n", tmpValueID->GetNodeId());
		if (content["command"] == "on" ) {
			Manager::Get()->SetValue(*tmpValueID , true);
			return "255";
		} else if (content["command"] == "off" ) {
			Manager::Get()->SetValue(*tmpValueID, false);
			return "0";
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
	 	stringstream ourNodeId;
		ourNodeId << Manager::Get()->GetControllerNodeId(g_homeId);


		agoConnection->addDevice(ourNodeId.str().c_str(), "zwavecontroller");
		agoConnection->addHandler(commandHandler);

		agoConnection->run();
	} else {
		printf("unable to initialize OZW\n");
	}	
	Manager::Destroy();

	pthread_mutex_destroy( &g_criticalSection );
	return 0;
}

