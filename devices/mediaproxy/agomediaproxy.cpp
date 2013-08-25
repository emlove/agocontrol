// Copyright (c) 2013 Harald Klein <hari@vt100.at>
// Copyright (c) 1996-2013, Live Networks, Inc.  All rights reserved

#include <string>
#include <pthread.h>

#include "liveMedia.hh"
#include "BasicUsageEnvironment.hh"
#include "agoclient.h"

using namespace std;
using namespace agocontrol;

char const* progName;
UsageEnvironment* env;
UserAuthenticationDatabase* authDB;

// Default values of command-line parameters:
int verbosityLevel = 0;
Boolean streamRTPOverTCP = False;
int http_port = 0;
int rtsp_port = 0;
portNumBits tunnelOverHTTPPortNum = 0;
std::string username;
std::string password;
Boolean proxyREGISTERRequests = False;
char stopLoop = 0;

AgoConnection *agoConnection;

static RTSPServer* createRTSPServer(Port port) {
	return RTSPServer::createNew(*env, port, authDB);
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	string internalid = content["internalid"].asString();
	if (internalid == "controller" && content["command"].asString() == "restart") {
		printf("restarting proxy\n");
		stopLoop = 1;
	}
	returnval["result"]=0;
	return returnval;
}
typedef struct { std::string username; std::string password; std::map<std::string, std::string> streams;} proxyparams;

proxyparams params;



void *startProxy(void *params) {
	// Increase the maximum size of video frames that we can 'proxy' without truncation.
	// (Such frames are unreasonably large; the back-end servers should really not be sending frames this large!)
	OutPacketBuffer::maxSize = 100000; // bytes

	// Begin by setting up our usage environment:
	TaskScheduler* scheduler = BasicTaskScheduler::createNew();
	env = BasicUsageEnvironment::createNew(*scheduler);

	*env << "ago control media proxy - "
	<< "(LIVE555 Streaming Media library version "
	<< LIVEMEDIA_LIBRARY_VERSION_STRING << ")\n\n";


	streamRTPOverTCP = True;

	authDB = NULL;
#ifdef ACCESS_CONTROL
	// To implement client access control to the RTSP server, do the following:
	authDB = new UserAuthenticationDatabase;
	authDB->addUserRecord("username1", "password1"); // replace these with real strings
	// Repeat the above with each <username>, <password> that you wish to allow
	// access to the server.
#endif
	// Create the RTSP server.
	RTSPServer* rtspServer;
	portNumBits rtspServerPortNum = rtsp_port;
	rtspServer = createRTSPServer(rtspServerPortNum);
	if (rtspServer == NULL) {
		*env << "Failed to create RTSP server: " << env->getResultMsg() << "\n";
		exit(1);
	}

	// Also, attempt to create a HTTP server for RTSP-over-HTTP tunneling.
	if (rtspServer->setUpTunnelingOverHTTP(http_port)) {
		*env << "\n(We use port " << rtspServer->httpServerPortNum() << " for optional RTSP-over-HTTP tunneling.)\n";
	} else {
		*env << "Failed to enable RTSP-over-HTTP tunneling\n";
		exit(1);
	}

	// Now, enter the event loop:
	while (true) {
		qpid::types::Variant::Map inventory = agoConnection->getInventory();
		qpid::types::Variant::Map devices = inventory["inventory"].asMap();

		for (qpid::types::Variant::Map::const_iterator it = devices.begin(); it != devices.end(); it++) {
			qpid::types::Variant::Map device = it->second.asMap();
			if (device["devicetype"] == "onvifnvt") {
				printf("found ONVIF NVT: %s\n", device["internalid"].asString().c_str());
				std::string streamname = it->first;
				std::string url = device["internalid"].asString();
				ServerMediaSession* sms = ProxyServerMediaSession::createNew(*env, rtspServer,
								   url.c_str(), streamname.c_str(),
								   username.c_str(), password.c_str(), tunnelOverHTTPPortNum, verbosityLevel);
				rtspServer->addServerMediaSession(sms);

				char* proxyStreamURL = rtspServer->rtspURL(sms);
				*env << "RTSP stream, proxying the stream \"" << url.c_str() << "\"\n";
				*env << "\tPlay this stream using the URL: " << proxyStreamURL << "\n";
				delete[] proxyStreamURL;
			}
		}	
		env->taskScheduler().doEventLoop(&stopLoop); // does not return
		printf("Exited event loop\n");
		stopLoop=0;
	}

	return NULL;
}

int main(int argc, char** argv) {
	username = getConfigOption("onvif", "username", "onvif");
	password = getConfigOption("onvif", "password", "onvif");
	verbosityLevel = atoi(getConfigOption("mediaproxy", "verbosity", "1").c_str());
	http_port = atoi(getConfigOption("mediaproxy", "http_port", "8888").c_str());
	rtsp_port = atoi(getConfigOption("mediaproxy", "rtsp_port", "554").c_str());

	agoConnection = new AgoConnection("mediaproxy");		
	printf("connection to agocontrol established\n");

	agoConnection->addDevice("controller", "mediaproxycontroller");

	agoConnection->addHandler(commandHandler);

	static pthread_t proxyThread;
	pthread_create(&proxyThread,NULL,startProxy,&params);

	printf("waiting for messages\n");
	agoConnection->run();

	return 0; // only to prevent compiler warning
}
