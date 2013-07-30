#include <stdio.h>
#include <string>
#include <map>

#include <uuid/uuid.h>

#include "soapMediaBindingProxy.h"
#include "soapDeviceBindingProxy.h"
#include "soapwsddProxy.h"
#include "onvif.nsmap"
#include "stdsoap2.h"
#include "soapStub.h"

#include "wsseapi.h"
#include "wsaapi.h"

#include "agoclient.h"

using namespace std;
using namespace agocontrol;

std::string getRTSPUri(std::string mediaXaddr, std::string username, std::string password, std::string profile) {
	std::string uri;

	MediaBindingProxy mediaProxy(mediaXaddr.c_str());

	_trt__GetStreamUri trt__GetStreamUri;
	_trt__GetStreamUriResponse trt__GetStreamUriResponse;
	
	tt__StreamSetup streamSetup;
	tt__ReferenceToken referenceToken;

	// we want a RTP unicast
	tt__StreamType streamType = tt__StreamType__RTP_Unicast;
	// via UDP transport
	tt__TransportProtocol transportProtocol = tt__TransportProtocol__UDP;
	tt__Transport transport;

	transport.Protocol = transportProtocol;
	streamSetup.Stream  = streamType;
	streamSetup.Transport  = &transport;

	trt__GetStreamUri.StreamSetup = &streamSetup;
	trt__GetStreamUri.ProfileToken = profile.c_str();

	soap_wsse_add_Security(&mediaProxy);
	soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());

	int result = mediaProxy.GetStreamUri(&trt__GetStreamUri, &trt__GetStreamUriResponse);
#ifdef DEBUG
	printf("SOAP Result: %d\n", result);
#endif
	if (result == SOAP_OK) {
#ifdef DEBUG
		printf("Stream: %s\n", trt__GetStreamUriResponse.MediaUri->Uri.c_str());
#endif
		uri = trt__GetStreamUriResponse.MediaUri->Uri;
	} else {
		printf("ERROR: GetStreamUri: %s\n", mediaProxy.soap_fault_detail());
		uri = "";
	}
	mediaProxy.destroy();
	return uri;
}

std::map <std::string, std::string> getProfiles(std::string mediaXaddr, std::string username, std::string password) {
	std::map<std::string, std::string> profiles;

	MediaBindingProxy mediaProxy(mediaXaddr.c_str());

	_trt__GetProfiles trt__GetProfiles;
	_trt__GetProfilesResponse trt__GetProfilesResponse;

	soap_wsse_add_Security(&mediaProxy);
	soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());

	int result = mediaProxy.GetProfiles (&trt__GetProfiles, &trt__GetProfilesResponse);
#ifdef DEBUG
        printf("SOAP Result: %d\n", result);
#endif
	if (result == SOAP_OK) {
		for(std::vector<tt__Profile * >::const_iterator it = trt__GetProfilesResponse.Profiles.begin(); it != trt__GetProfilesResponse.Profiles.end(); ++it) {
			tt__Profile* profile = *it;
			profiles[profile->token]=profile->Name;
#ifdef DEBUG
			printf("Profile: %s: %s\n", profile->token.c_str(), profile->Name.c_str());
#endif
		}
	} else {
		printf("ERROR: GetProfiles: %s\n", mediaProxy.soap_fault_detail());
	}
	mediaProxy.destroy();
	return profiles;
}

int getCapabilities(std::string deviceXaddr, std::string username, std::string password, _tds__GetCapabilitiesResponse &response) {
        DeviceBindingProxy deviceProxy(deviceXaddr.c_str());

	_tds__GetCapabilities tds__GetCapabilities;

	soap_wsse_add_Security(&deviceProxy);
	soap_wsse_add_UsernameTokenDigest(&deviceProxy, NULL, username.c_str(), password.c_str());

	int result =deviceProxy.GetCapabilities(&tds__GetCapabilities, &response);
#ifdef DEBUG
        printf("SOAP Result: %d\n", result);
#endif
	/* if (result == SOAP_OK) {
		printf("Media Service: %s\n",tds__GetCapabilitiesResponse.Capabilities->Media->XAddr.c_str());
	} else {
		printf("ERROR: GetCapabilities: %s\n", deviceProxy.soap_fault_detail());
	} */
	deviceProxy.destroy();
	return result;
}

void getDeviceInformation(std::string deviceXaddr, std::string username, std::string password) {
        DeviceBindingProxy deviceProxy(deviceXaddr.c_str());

	_tds__GetDeviceInformation tds__GetDeviceInformation;
	_tds__GetDeviceInformationResponse tds__GetDeviceInformationResponse;

	soap_wsse_add_Security(&deviceProxy);
	soap_wsse_add_UsernameTokenDigest(&deviceProxy, NULL, username.c_str(), password.c_str());

	int result = deviceProxy.GetDeviceInformation(&tds__GetDeviceInformation, &tds__GetDeviceInformationResponse);
#ifdef DEBUG
        printf("SOAP Result: %d\n", result);
#endif
	if (result == SOAP_OK) {
			printf("Manufacturer: %s\n",tds__GetDeviceInformationResponse.Manufacturer.c_str());
			printf("Model: %s\n",tds__GetDeviceInformationResponse.Model.c_str());
			printf("FirmwareVersion: %s\n",tds__GetDeviceInformationResponse.FirmwareVersion.c_str());
			printf("Serial Number: %s\n",tds__GetDeviceInformationResponse.SerialNumber.c_str());
			printf("HardwareId: %s\n",tds__GetDeviceInformationResponse.HardwareId.c_str());
	} else {
		printf("ERROR: GetDeviceInformation: %s\n", deviceProxy.soap_fault_detail());
	}
	deviceProxy.destroy();
}

std::string commandHandler(qpid::types::Variant::Map content) {
	string internalid = content["internalid"].asString();
	return "";
}

int main (int argc, char ** argv)  
{  
	std::map<std::string, std::string> networkvideotransmitters; // this holds the probe results

	struct wsdd__ProbeType probe;
	struct __wsdd__ProbeMatches matches;
	probe.Scopes = new struct wsdd__ScopesType();
	probe.Types = (char*)"tdn:NetworkVideoTransmitter";

	for (int i=0;i<3;i++) {
		std::string tmpuuid = "urn:uuid:" +  generateUuid();

		wsddProxy *discoverProxy = new wsddProxy("soap.udp://239.255.255.250:3702/");
		discoverProxy->soap_header((char*)tmpuuid.c_str(), NULL, NULL, NULL, NULL, "urn:schemas-xmlsoap-org:ws:2005:04:discovery", "http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
		discoverProxy->recv_timeout=3;

		printf("Sending probe\n");
		discoverProxy->send_Probe(&probe);
		printf("waiting for matches\n");
		while ( discoverProxy->recv_ProbeMatches(matches) == SOAP_OK) {
			printf("Service Addr: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->XAddrs);
			//printf("Type: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->Types);
			//printf("Metadata Ver: %d\n",matches.wsdd__ProbeMatches->ProbeMatch->MetadataVersion);
			networkvideotransmitters[matches.wsdd__ProbeMatches->ProbeMatch->XAddrs] = matches.wsdd__ProbeMatches->ProbeMatch->Scopes->__item;

		}
		discoverProxy->destroy();
	}

	AgoConnection agoConnection = AgoConnection("onvif");		
	printf("connection to agocontrol established\n");

	for (std::map<std::string, std::string>::const_iterator it = networkvideotransmitters.begin(); it != networkvideotransmitters.end(); ++it) {
		printf("Found: %s - \n", it->first.c_str(), it->second.c_str());

		std::string deviceService = it->first;
		std::string m_username = "onvif";
		std::string m_password = "onvif";
		std::string mediaService;

		getDeviceInformation(deviceService, m_username, m_password);
		_tds__GetCapabilitiesResponse response;
		if ( getCapabilities(deviceService, m_username, m_password, response) == SOAP_OK) {
			mediaService= response.Capabilities->Media->XAddr.c_str(); // segfaults on direct std::string = std::string assignment??
			//printf("Mediaservice: %s\n",mediaService.c_str());

			std::map <std::string, std::string> profiles;
			profiles = getProfiles(mediaService, m_username, m_password);
			std::map <std::string, std::string>::const_iterator it = profiles.find("balanced_h264");
			if (it != profiles.end()) { // cam supports balanced_h264 profile, get the URI
				printf("URI: %s\n", getRTSPUri(mediaService, m_username, m_password, "balanced_h264").c_str());
				agoConnection.addDevice(getRTSPUri(mediaService, m_username, m_password, "balanced_h264").c_str(), "onvifnvt");
			}
		}
	}

	agoConnection.addHandler(commandHandler);

	printf("waiting for messages\n");
	agoConnection.run();
} 
