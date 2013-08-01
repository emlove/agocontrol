#include <stdio.h>
#include <string>
#include <sstream>
#include <vector>
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
			printf("Manufacturer: %s ",tds__GetDeviceInformationResponse.Manufacturer.c_str());
			printf("Model: %s ",tds__GetDeviceInformationResponse.Model.c_str());
			printf("FirmwareVersion: %s ",tds__GetDeviceInformationResponse.FirmwareVersion.c_str());
			printf("Serial Number: %s ",tds__GetDeviceInformationResponse.SerialNumber.c_str());
			printf("HardwareId: %s\n",tds__GetDeviceInformationResponse.HardwareId.c_str());
	} else {
		printf("ERROR: GetDeviceInformation: %s\n", deviceProxy.soap_fault_detail());
	}
	deviceProxy.destroy();
}

bool checkDateTime(std::string deviceXaddr) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
	deviceProxy.recv_timeout=3;

	_tds__GetSystemDateAndTime request;
	_tds__GetSystemDateAndTimeResponse response;
	int result = deviceProxy.GetSystemDateAndTime(&request, &response);
	if (result == SOAP_OK) {
		printf("Daylight savings: %d\n", response.SystemDateAndTime->DaylightSavings);
		printf("Timezone: %s\n", response.SystemDateAndTime->TimeZone->TZ.c_str());
		printf("Time: %d:%d:%d\n", response.SystemDateAndTime->LocalDateTime->Time->Hour, 
						response.SystemDateAndTime->LocalDateTime->Time->Minute,
						response.SystemDateAndTime->LocalDateTime->Time->Second);
		printf("Date: %d-%d-%d\n", response.SystemDateAndTime->LocalDateTime->Date->Year, 
						response.SystemDateAndTime->LocalDateTime->Date->Month,
						response.SystemDateAndTime->LocalDateTime->Date->Day);
		deviceProxy.destroy();
		return true;
	} else {
                printf("ERROR: %d GetSystemDateAndTime: %s\n", result, deviceProxy.soap_fault_detail());
		deviceProxy.destroy();
		return false;
	}
}

bool getUsers(std::string deviceXaddr) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
	_tds__GetUsers request;
	_tds__GetUsersResponse response;

	int result = deviceProxy.GetUsers(&request, &response);
	if (result == SOAP_OK) {
		for(std::vector<tt__User * >::const_iterator it = response.User.begin(); it != response.User.end(); it++) {
			printf("Username found: %s\n", (*it)->Username.c_str());
		}
	} else {
                printf("ERROR: %d GetUsers: %s\n", result, deviceProxy.soap_fault_detail());
                deviceProxy.destroy();
                return false;
        }


	return true;
}
bool createUser(std::string deviceXaddr, std::string username, std::string password, int level) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
	tt__User user;
	std::string m_username = username;
	std::string m_password = password;
	user.Username = m_username;
	user.Password = &m_password;
	// enum tt__UserLevel { tt__UserLevel__Administrator = 0, tt__UserLevel__Operator = 1, tt__UserLevel__User = 2, tt__UserLevel__Anonymous = 3, tt__UserLevel__Extended = 4 };
	user.UserLevel = tt__UserLevel__Administrator;

	std::vector<tt__User *> users;
	users.push_back(&user);
	_tds__CreateUsers request;
	request.User = users;
	_tds__CreateUsersResponse response;
	int result = deviceProxy.CreateUsers(&request, &response);
	if (result == SOAP_OK) {
		printf("USER CREATED\n");
	} else {
                printf("ERROR: %d CreateUsers: %s\n", result, deviceProxy.soap_fault_detail());
                deviceProxy.destroy();
                return false;
        }


	
	deviceProxy.destroy();
	return true;

}
std::string commandHandler(qpid::types::Variant::Map content) {
	string internalid = content["internalid"].asString();
	return "";
}

int main (int argc, char ** argv)  
{  
	std::map<std::string, std::string> networkvideotransmitters; // this holds the probe results
	std::string m_username = getConfigOption("onvif", "username", "onvif");
	std::string m_password = getConfigOption("onvif", "password", "onvif");
	std::string targetprofile = getConfigOption("onvif", "profile", "balanced_h264");

	struct wsdd__ProbeType probe;
	struct __wsdd__ProbeMatches matches;
	probe.Scopes = new struct wsdd__ScopesType();
	probe.Types = (char*)"tdn:NetworkVideoTransmitter";

	for (int i=0;i<2;i++) {
		std::string tmpuuid = "urn:uuid:" +  generateUuid();

		wsddProxy *discoverProxy = new wsddProxy("soap.udp://239.255.255.250:3702/");
		discoverProxy->soap_header((char*)tmpuuid.c_str(), NULL, NULL, NULL, NULL, (char*)"urn:schemas-xmlsoap-org:ws:2005:04:discovery", (char*)"http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
		discoverProxy->recv_timeout=2;

		printf("Sending probe\n");
		discoverProxy->send_Probe(&probe);
//		printf("waiting for matches\n");
		while ( discoverProxy->recv_ProbeMatches(matches) == SOAP_OK) {
			//printf("Service Addr: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->XAddrs);
			// printf("Type: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->Types);
			//printf("Metadata Ver: %d\n",matches.wsdd__ProbeMatches->ProbeMatch->MetadataVersion);
			stringstream addrs(matches.wsdd__ProbeMatches->ProbeMatch->XAddrs);
			string addr;
			while (getline(addrs, addr, ' ')) {
				if (addr.find("169.254.") == std::string::npos) { // ignore ipv4 link local XAddrs
					networkvideotransmitters[addr] = matches.wsdd__ProbeMatches->ProbeMatch->Scopes->__item;
				} else {
					printf("ignoring link local addr %s\n", addr.c_str());
				}
			}
		}
		discoverProxy->destroy();
	}

	AgoConnection agoConnection = AgoConnection("onvif");		
	printf("connection to agocontrol established\n");

	for (std::map<std::string, std::string>::const_iterator it = networkvideotransmitters.begin(); it != networkvideotransmitters.end(); ++it) {
		printf("Found: %s - \n", it->first.c_str(), it->second.c_str());

		std::string deviceService = it->first;
		std::string mediaService;

		printf("sending ONVIF GetSystemDateTime request to %s\n", deviceService.c_str());
		if (checkDateTime(deviceService)) {
			getUsers(deviceService);
			createUser(deviceService, m_username, m_password, 0);
			getDeviceInformation(deviceService, m_username, m_password);
			_tds__GetCapabilitiesResponse response;
			if ( getCapabilities(deviceService, m_username, m_password, response) == SOAP_OK) {
				mediaService= response.Capabilities->Media->XAddr.c_str(); // segfaults on direct std::string = std::string assignment??
				//printf("Mediaservice: %s\n",mediaService.c_str());

				std::map <std::string, std::string> profiles;
				profiles = getProfiles(mediaService, m_username, m_password);
				for (std::map <std::string, std::string>::const_iterator it = profiles.begin(); it != profiles.end(); it++) {
					printf("Profile: %s\n", it->first.c_str());
				}
				std::map <std::string, std::string>::const_iterator it = profiles.find(targetprofile);
				if (it != profiles.end()) { // cam supports wanted profile, get the URI
					printf("URI: %s\n", getRTSPUri(mediaService, m_username, m_password, targetprofile).c_str());
					agoConnection.addDevice(getRTSPUri(mediaService, m_username, m_password, targetprofile).c_str(), "onvifnvt");
				} else { // take the first profile otherwise
					it = profiles.begin();
					if (it != profiles.end()) {
						printf("URI: %s\n", getRTSPUri(mediaService, m_username, m_password, it->first).c_str());
						agoConnection.addDevice(getRTSPUri(mediaService, m_username, m_password, it->first).c_str(), "onvifnvt");
					}
				}
			}
		} else {
			printf("ERROR: ONVIF GetSystemDateTime request to %s did fail!\n", deviceService.c_str());
		}
	}

	agoConnection.addHandler(commandHandler);

	printf("waiting for messages\n");
	agoConnection.run();
} 
