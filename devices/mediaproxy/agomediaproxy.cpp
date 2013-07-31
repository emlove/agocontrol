// Copyright (c) 2013 Harald Klein <hari@vt100.at>
// Copyright (c) 1996-2013, Live Networks, Inc.  All rights reserved

#include <string>
#include "liveMedia.hh"
#include "BasicUsageEnvironment.hh"

char const* progName;
UsageEnvironment* env;
UserAuthenticationDatabase* authDB;

// Default values of command-line parameters:
int verbosityLevel = 0;
Boolean streamRTPOverTCP = False;
portNumBits tunnelOverHTTPPortNum = 0;
char* username = NULL;
char* password = NULL;
Boolean proxyREGISTERRequests = False;

static RTSPServer* createRTSPServer(Port port) {
	return RTSPServer::createNew(*env, port, authDB);
}

int main(int argc, char** argv) {
	// Increase the maximum size of video frames that we can 'proxy' without truncation.
	// (Such frames are unreasonably large; the back-end servers should really not be sending frames this large!)
	OutPacketBuffer::maxSize = 100000; // bytes

	// Begin by setting up our usage environment:
	TaskScheduler* scheduler = BasicTaskScheduler::createNew();
	env = BasicUsageEnvironment::createNew(*scheduler);

	*env << "ago control media proxy - "
	<< "(LIVE555 Streaming Media library version "
	<< LIVEMEDIA_LIBRARY_VERSION_STRING << ")\n\n";

	verbosityLevel = 1;
	verbosityLevel = 2;

	streamRTPOverTCP = True;

	username = "onvif";
	password = "onvif";

	authDB = NULL;
#ifdef ACCESS_CONTROL
	// To implement client access control to the RTSP server, do the following:
	authDB = new UserAuthenticationDatabase;
	authDB->addUserRecord("username1", "password1"); // replace these with real strings
	// Repeat the above with each <username>, <password> that you wish to allow
	// access to the server.
#endif

	// Create the RTSP server.  Try first with the default port number (554),
	// and then with the alternative port number (8554):
	RTSPServer* rtspServer;
	portNumBits rtspServerPortNum = 554;
	rtspServer = createRTSPServer(rtspServerPortNum);
	if (rtspServer == NULL) {
		*env << "Failed to create RTSP server: " << env->getResultMsg() << "\n";
		exit(1);
	}

	std::string streamname;
	std::string url;
	streamname= "1234";
	url="rtsp://192.168.80.65/axis/media.amp";

	ServerMediaSession* sms = ProxyServerMediaSession::createNew(*env, rtspServer,
					   url.c_str(), streamname.c_str(),
					   username, password, tunnelOverHTTPPortNum, verbosityLevel);
	rtspServer->addServerMediaSession(sms);

	char* proxyStreamURL = rtspServer->rtspURL(sms);
	*env << "RTSP stream, proxying the stream \"" << url.c_str() << "\"\n";
	*env << "\tPlay this stream using the URL: " << proxyStreamURL << "\n";
	delete[] proxyStreamURL;

	// Also, attempt to create a HTTP server for RTSP-over-HTTP tunneling.
	// Try first with the default HTTP port (80), and then with the alternative HTTP
	// port numbers (8000 and 8080).

	if (rtspServer->setUpTunnelingOverHTTP(8888)) {
		*env << "\n(We use port " << rtspServer->httpServerPortNum() << " for optional RTSP-over-HTTP tunneling.)\n";
	} else {
		*env << "\n(RTSP-over-HTTP tunneling is not available.)\n";
	}

	// Now, enter the event loop:
	env->taskScheduler().doEventLoop(); // does not return

	return 0; // only to prevent compiler warning
}
