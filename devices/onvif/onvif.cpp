#include <stdio.h>
#include <string>
#include <sstream>
#include <vector>
#include <map>
#include <time.h>
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
	if (result == SOAP_OK) {
		uri = trt__GetStreamUriResponse.MediaUri->Uri;
	} else {
		printf("ERROR: %d - GetStreamUri: %s\n", result, mediaProxy.soap_fault_detail());
		uri = "";
	}
	mediaProxy.destroy();
	return uri;
}

bool deleteProfile(std::string mediaXaddr, std::string username, std::string password, std::string token) {
        MediaBindingProxy mediaProxy(mediaXaddr.c_str());

        soap_wsse_add_Security(&mediaProxy);
        soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());

        _trt__DeleteProfile request;
        _trt__DeleteProfileResponse response;

	request.ProfileToken = token;

        int result = mediaProxy.DeleteProfile(&request, &response);
        if (result == SOAP_OK) {
                printf("profile deleted\n");
        } else {
                printf("ERROR: %d - DeleteProfile: %s\n", result, mediaProxy.soap_fault_detail());
                mediaProxy.destroy();
                return false;
        }
        mediaProxy.destroy();
        return true;
}

std::vector < tt__AudioSourceConfiguration * > getAudioSourceConfigurations(std::string mediaXaddr, std::string username, std::string password) {
        MediaBindingProxy mediaProxy(mediaXaddr.c_str());

        soap_wsse_add_Security(&mediaProxy);
        soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());

	_trt__GetAudioSourceConfigurations request;
	_trt__GetAudioSourceConfigurationsResponse response;
	
	int result = mediaProxy.GetAudioSourceConfigurations(&request, &response);
        if (result != SOAP_OK) {
                printf("ERROR: %d - DeleteProfile: %s\n", result, mediaProxy.soap_fault_detail());
        }
	mediaProxy.destroy();
	return response.Configurations;
}

bool createProfile(std::string mediaXaddr, std::string username, std::string password) {
        MediaBindingProxy mediaProxy(mediaXaddr.c_str());

        soap_wsse_add_Security(&mediaProxy);
        soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());

	_trt__CreateProfile request;
	_trt__CreateProfileResponse response;

	request.Name = "AgoVIEW profile";
	tt__ReferenceToken token;
	token = "p-agoview";
	request.Token = &token;

	int result = mediaProxy.CreateProfile(&request, &response);
	if (result == SOAP_OK) {
		printf("profile created\n");
		_trt__GetVideoSourceConfigurations request;
		_trt__GetVideoSourceConfigurationsResponse response;
		soap_wsse_add_Security(&mediaProxy);
		soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());
		int result2 = mediaProxy.GetVideoSourceConfigurations(&request, &response);
		if (result2 == SOAP_OK) {
			for (std::vector < tt__VideoSourceConfiguration * >::const_iterator it = response.Configurations.begin(); it!=response.Configurations.end(); it++) {
				printf("Source Token: %s ", (*it)->SourceToken.c_str());
				printf("Bounds: x:%d y:%d w: %d h: %d ", (*it)->Bounds->x, (*it)->Bounds->y, (*it)->Bounds->width, (*it)->Bounds->height);
				if ((*it)->Extension != NULL)  { // enum tt__RotateMode { tt__RotateMode__OFF = 0, tt__RotateMode__ON = 1, tt__RotateMode__AUTO = 2 };
					printf("Rotate: %ddeg mode: %d\n", (*it)->Extension->Rotate->Degree, (*it)->Extension->Rotate->Mode);
				}
				printf("\n");
				if (it==response.Configurations.begin()) {
					// use first source for our profile
					_trt__AddVideoSourceConfiguration addSourceRequest;
					_trt__AddVideoSourceConfigurationResponse addSourceResponse;
					addSourceRequest.ProfileToken = token;
					addSourceRequest.ConfigurationToken = (*it)->SourceToken;
					soap_wsse_add_Security(&mediaProxy);
					soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());
					int result3 = mediaProxy.AddVideoSourceConfiguration(&addSourceRequest, &addSourceResponse);
					if (result3 == SOAP_OK) {
						printf("Source Configuration added to Profile\n");
					} else {
						printf("ERROR: %d - AddVideoSourceConfiguration: %s\n", result3, mediaProxy.soap_fault_detail());
					}
				}
			}
		} else {
			printf("ERROR: %d - GetVideoSourceConfigurations: %s\n", result2, mediaProxy.soap_fault_detail());
			return false;
		}
		_trt__GetVideoEncoderConfigurations encoderRequest;
		_trt__GetVideoEncoderConfigurationsResponse encoderResponse;
		soap_wsse_add_Security(&mediaProxy);
                soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());
                result2 = mediaProxy.GetVideoEncoderConfigurations(&encoderRequest, &encoderResponse);
                if (result2 == SOAP_OK) {
                        for (std::vector < tt__VideoEncoderConfiguration *>::const_iterator it = encoderResponse.Configurations.begin(); it!=encoderResponse.Configurations.end(); it++) {
				if ((*it)->Encoding != tt__VideoEncoding__H264) continue; // skip all non-h264 for now
				std::string encoding;
				switch((*it)->Encoding) {
					case tt__VideoEncoding__JPEG: encoding = "JPEG"; break;
					case tt__VideoEncoding__MPEG4: encoding = "MPEG4"; break;
					case tt__VideoEncoding__H264: encoding = "H264"; break;
					default: break;
				}
				printf("Token: %s\n", (*it)->token.c_str());
				printf("Encoding: %s ", encoding.c_str());
				printf("Resolution: %dx%d ", (*it)->Resolution->Width, (*it)->Resolution->Height);
				printf("Quality: %f\n", (*it)->Quality);
			}
			for (std::vector < tt__VideoEncoderConfiguration *>::const_iterator it = encoderResponse.Configurations.begin(); it!=encoderResponse.Configurations.end(); it++) {
				if ((*it)->Encoding == tt__VideoEncoding__H264) {
					_trt__AddVideoEncoderConfiguration videoEncoderRequest;
					_trt__AddVideoEncoderConfigurationResponse videoEncoderResponse;
					videoEncoderRequest.ProfileToken = token;
					videoEncoderRequest.ConfigurationToken = (*it)->token;

					soap_wsse_add_Security(&mediaProxy);
                                        soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());
					int result3 = mediaProxy.AddVideoEncoderConfiguration(&videoEncoderRequest, &videoEncoderResponse);
                         	        if (result3 == SOAP_OK) {
                                                printf("Encoder Configuration added to Profile\n");
                                        } else {
                                                printf("ERROR: %d - AddVideoEncoderConfiguration: %s\n", result3, mediaProxy.soap_fault_detail());
                                        }
					break;
				}
			}
		} else {
			printf("ERROR: %d - GetVideoEncoderConfigurations: %s\n", result2, mediaProxy.soap_fault_detail());
			return false;
		}
		std::vector < tt__AudioSourceConfiguration * > audioConfigs = getAudioSourceConfigurations(mediaXaddr, username, password);
		for (std::vector < tt__AudioSourceConfiguration * >::const_iterator it = audioConfigs.begin(); it!=audioConfigs.end(); it++) {
			printf("AudioSourceConfiguration: %s\n", (*it)->SourceToken.c_str());
		}
	} else {
		printf("ERROR: %d - CreateProfile: %s\n", result, mediaProxy.soap_fault_detail());
		mediaProxy.destroy();
		return false;
	}
	mediaProxy.destroy();
	return true;
} 

std::map <std::string, std::string> getProfiles(std::string mediaXaddr, std::string username, std::string password) {
	std::map<std::string, std::string> profiles;

	MediaBindingProxy mediaProxy(mediaXaddr.c_str());

	_trt__GetProfiles trt__GetProfiles;
	_trt__GetProfilesResponse trt__GetProfilesResponse;

	soap_wsse_add_Security(&mediaProxy);
	soap_wsse_add_UsernameTokenDigest(&mediaProxy, NULL, username.c_str(), password.c_str());

	int result = mediaProxy.GetProfiles (&trt__GetProfiles, &trt__GetProfilesResponse);
	if (result == SOAP_OK) {
		for(std::vector<tt__Profile * >::const_iterator it = trt__GetProfilesResponse.Profiles.begin(); it != trt__GetProfilesResponse.Profiles.end(); ++it) {
			tt__Profile* profile = *it;
			profiles[profile->token]=profile->Name;
			printf("Profile: %s: %s - fixed: %d ", profile->token.c_str(), profile->Name.c_str(), *(profile->fixed));
			if (profile->VideoEncoderConfiguration!=NULL) {
				// enum tt__VideoEncoding { tt__VideoEncoding__JPEG = 0, tt__VideoEncoding__MPEG4 = 1, tt__VideoEncoding__H264 = 2 };
				std::string encoding;
				switch(profile->VideoEncoderConfiguration->Encoding) {
					case tt__VideoEncoding__JPEG: encoding = "JPEG"; break;
					case tt__VideoEncoding__MPEG4: encoding = "MPEG4"; break;
					case tt__VideoEncoding__H264: encoding = "H264"; break;
					default: break;
				}

				int x,y;
				x=profile->VideoEncoderConfiguration->Resolution->Width;
				y=profile->VideoEncoderConfiguration->Resolution->Height;
				printf("Codec: %s Resolution: %dx%d ",encoding.c_str(),x,y); 
				if (profile->VideoEncoderConfiguration->RateControl != NULL) {
					printf("FPS Limit: %d EncInt: %d BitrateLimit: %d ", profile->VideoEncoderConfiguration->RateControl->FrameRateLimit, profile->VideoEncoderConfiguration->RateControl->EncodingInterval, profile->VideoEncoderConfiguration->RateControl->BitrateLimit); 
				}
			}
			printf("\n");
		}
	} else {
		printf("ERROR: %d - GetProfiles: %s\n", result, mediaProxy.soap_fault_detail());
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
	if (result != SOAP_OK) {
		printf("ERROR: %d - GetCapabilities: %s\n", result, deviceProxy.soap_fault_detail());
	} 
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
	if (result == SOAP_OK) {
			printf("DEVICE INFORMATION: Manufacturer: %s ",tds__GetDeviceInformationResponse.Manufacturer.c_str());
			printf("Model: %s ",tds__GetDeviceInformationResponse.Model.c_str());
			printf("FirmwareVersion: %s ",tds__GetDeviceInformationResponse.FirmwareVersion.c_str());
			printf("Serial Number: %s ",tds__GetDeviceInformationResponse.SerialNumber.c_str());
			printf("HardwareId: %s\n",tds__GetDeviceInformationResponse.HardwareId.c_str());
	} else {
		printf("ERROR: %d - GetDeviceInformation: %s\n", result, deviceProxy.soap_fault_detail());
	}
	deviceProxy.destroy();
}

bool setSystemDateAndTime(std::string deviceXaddr, std::string username, std::string password, long offset, const char *timezone, bool dst) {
        DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
        _tds__SetSystemDateAndTime request;
        _tds__SetSystemDateAndTimeResponse response;

	soap_wsse_add_Security(&deviceProxy);
	soap_wsse_add_UsernameTokenDigestOffset(&deviceProxy, NULL, username.c_str(), password.c_str(), offset);

	request.DateTimeType = tt__SetDateTimeType__NTP;
	request.DaylightSavings = dst;
	tt__TimeZone tz;
	tz.TZ = std::string(timezone);
	request.TimeZone = &tz;

	int result = deviceProxy.SetSystemDateAndTime(&request, &response);
	if (result == SOAP_OK) {
		printf("System Date and Time set successfully\n");
		deviceProxy.destroy();
		return true;
	} else {
                printf("ERROR: %d - SetSystemDateAndTime: %s\n", result, deviceProxy.soap_fault_detail());
		deviceProxy.destroy();
		return false;
	}
	return false;
}


bool checkDateTime(std::string deviceXaddr, long *offset) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
	deviceProxy.recv_timeout=3;

	_tds__GetSystemDateAndTime request;
	_tds__GetSystemDateAndTimeResponse response;
	int result = deviceProxy.GetSystemDateAndTime(&request, &response);
	if (result == SOAP_OK) {
		printf("DST: %d ", response.SystemDateAndTime->DaylightSavings);
		printf("TZ: %s ", response.SystemDateAndTime->TimeZone->TZ.c_str());
		printf("NTP: %s ", response.SystemDateAndTime->DateTimeType == 0 ? "yes" : "no");
		printf("Date: %4d-%2d-%2d - ", response.SystemDateAndTime->LocalDateTime->Date->Year, 
						response.SystemDateAndTime->LocalDateTime->Date->Month,
						response.SystemDateAndTime->LocalDateTime->Date->Day);
		printf("Time: %2d:%2d:%2d ", response.SystemDateAndTime->LocalDateTime->Time->Hour, 
						response.SystemDateAndTime->LocalDateTime->Time->Minute,
						response.SystemDateAndTime->LocalDateTime->Time->Second);
		struct tm camtimestruct;
		camtimestruct.tm_sec = response.SystemDateAndTime->LocalDateTime->Time->Second;
		camtimestruct.tm_min = response.SystemDateAndTime->LocalDateTime->Time->Minute;
		camtimestruct.tm_hour = response.SystemDateAndTime->LocalDateTime->Time->Hour;
		camtimestruct.tm_mday = response.SystemDateAndTime->LocalDateTime->Date->Day;
		camtimestruct.tm_mon = response.SystemDateAndTime->LocalDateTime->Date->Month -1;
		camtimestruct.tm_year = response.SystemDateAndTime->LocalDateTime->Date->Year - 1900;
		camtimestruct.tm_isdst = response.SystemDateAndTime->DaylightSavings;

		char *tz;
		tz = getenv("TZ");
		setenv("TZ", response.SystemDateAndTime->TimeZone->TZ.c_str(), 1);
		tzset();

		time_t camtime = mktime(&camtimestruct);

		if (tz)
			setenv("TZ", tz, 1);
		else
			unsetenv("TZ");
		tzset();
#ifdef DEBUG
		// printf("Cam Time: %d\n", camtime);
		// printf("local Time: %d\n", time(NULL));
		printf("Offset: %d\n", camtime - time(NULL));
#endif
		if (offset != NULL) *offset=(long)(camtime - time(NULL));
		// if (response.SystemDateAndTime->DaylightSavings == 0) *offset+=3600;
		deviceProxy.destroy();
		return true;
	} else {
                printf("ERROR: %d - GetSystemDateAndTime: %s\n", result, deviceProxy.soap_fault_detail());
		deviceProxy.destroy();
		return false;
	}
}

bool getUsers(std::string deviceXaddr) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
	_tds__GetUsers request;
	_tds__GetUsersResponse response;

	bool hasUsers = false;
	int result = deviceProxy.GetUsers(&request, &response);
	if (result == SOAP_OK) {
		for(std::vector<tt__User * >::const_iterator it = response.User.begin(); it != response.User.end(); it++) {
			printf("Username found: %s\n", (*it)->Username.c_str());
			hasUsers = true;
		}
	} else {
               // printf("ERROR: %d GetUsers: %s\n", result, deviceProxy.soap_fault_detail());
                deviceProxy.destroy();
                return true;
        }


	return hasUsers;
}
bool createUser(std::string deviceXaddr, std::string username, std::string password, tt__UserLevel level) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());
	tt__User user;
	std::string m_username = username;
	std::string m_password = password;
	user.Username = m_username;
	user.Password = &m_password;
	// enum tt__UserLevel { tt__UserLevel__Administrator = 0, tt__UserLevel__Operator = 1, tt__UserLevel__User = 2, tt__UserLevel__Anonymous = 3, tt__UserLevel__Extended = 4 };
	user.UserLevel = level;

	std::vector<tt__User *> users;
	users.push_back(&user);
	_tds__CreateUsers request;
	request.User = users;
	_tds__CreateUsersResponse response;
	int result = deviceProxy.CreateUsers(&request, &response);
	if (result == SOAP_OK) {
		printf("USER CREATED\n");
	} else {
                printf("ERROR: %d - CreateUsers: %s\n", result, deviceProxy.soap_fault_detail());
                deviceProxy.destroy();
                return false;
        }


	
	deviceProxy.destroy();
	return true;

}

bool getNTP(std::string deviceXaddr, std::string username, std::string password, long offset) {
	DeviceBindingProxy deviceProxy(deviceXaddr.c_str());

        _tds__GetNTP request;
        _tds__GetNTPResponse response;

	soap_wsse_add_Security(&deviceProxy);
        soap_wsse_add_UsernameTokenDigestOffset(&deviceProxy, NULL, username.c_str(), password.c_str(), offset);

        int result = deviceProxy.GetNTP(&request, &response);
	if (result == SOAP_OK) {
                printf("NTP Get successful\n");
		for (std::vector< tt__NetworkHost * >::const_iterator it = response.NTPInformation->NTPManual.begin(); it!=response.NTPInformation->NTPManual.end(); it++) {
			if ((*it)->DNSname != NULL) printf("DNS NAme: %s\n", (*it)->DNSname->c_str());
		}
        } else {
                printf("ERROR: %d - GetNTP: %s\n", result, deviceProxy.soap_fault_detail());
                deviceProxy.destroy();
                return false;
        }
        deviceProxy.destroy();
        return true;
}

bool setNTP(std::string deviceXaddr, std::string username, std::string password, long offset, const char *server) {
        DeviceBindingProxy deviceProxy(deviceXaddr.c_str());

	_tds__SetNTP request;
	_tds__SetNTPResponse response;

	std::vector<tt__NetworkHost * > hosts;
	tt__NetworkHost host;
	std::string hostname = server;
	host.IPv4Address = &hostname;
	// host.DNSname = &hostname;
	host.Type = tt__NetworkHostType__IPv4;
	// host.Type = tt__NetworkHostType__DNS;
	hosts.push_back(&host);
	request.NTPManual = hosts;
	request.FromDHCP = false;
	printf("setting NTP host to %s\n", hostname.c_str());
	soap_wsse_add_Security(&deviceProxy);
	soap_wsse_add_UsernameTokenDigestOffset(&deviceProxy, NULL, username.c_str(), password.c_str(), offset);

	int result = deviceProxy.SetNTP(&request, &response);
	if (result == SOAP_OK) {
		printf("NTP Set successful\n");
	} else {
                printf("ERROR: %d - SetNTP: %s\n", result, deviceProxy.soap_fault_detail());
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
	std::string targetprofile = getConfigOption("onvif", "profile", "p-agoview");

	struct wsdd__ProbeType probe;
	struct __wsdd__ProbeMatches matches;
	probe.Scopes = new struct wsdd__ScopesType();
	probe.Types = (char*)"tdn:NetworkVideoTransmitter";

	printf("Sending probes\n");
	for (int i=0;i<2;i++) {
		std::string tmpuuid = "urn:uuid:" +  generateUuid();

		wsddProxy *discoverProxy = new wsddProxy("soap.udp://239.255.255.250:3702/");
		discoverProxy->soap_header((char*)tmpuuid.c_str(), NULL, NULL, NULL, NULL, (char*)"urn:schemas-xmlsoap-org:ws:2005:04:discovery", (char*)"http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
		discoverProxy->recv_timeout=2;

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
				} /* else {
					printf("ignoring link local addr %s\n", addr.c_str());
				}*/
			}
		}
		discoverProxy->destroy();
	}

	AgoConnection agoConnection = AgoConnection("onvif");		
	printf("connection to agocontrol established\n");

	for (std::map<std::string, std::string>::const_iterator it = networkvideotransmitters.begin(); it != networkvideotransmitters.end(); ++it) {
		std::string deviceService = it->first;
		std::string mediaService;

		printf("sending ONVIF GetSystemDateTime request to %s: ", deviceService.c_str());
		long offset;
		if (checkDateTime(deviceService, &offset)) {
			if (getUsers(deviceService) == false) {
				printf("No users on device, starting initial configuration\n");
				createUser(deviceService, m_username, m_password, tt__UserLevel__Administrator);
				getNTP(deviceService, m_username, m_password, offset);
				setNTP(deviceService, m_username, m_password, offset, "86.59.80.170");
				sleep(3);
				checkDateTime(deviceService, &offset);
				setSystemDateAndTime(deviceService, m_username, m_password, offset, "CET-1CEST,M3.5.0,M10.5.0/3", 1);
				sleep(3);
				checkDateTime(deviceService, &offset);
			}
			if (abs(offset) > 10) {
				printf("WARNING -- TIME OFFSET DETECTED!!! Seconds: %d - trying to set NTP server\n", offset);
				setNTP(deviceService, m_username, m_password, offset, "86.59.80.170");
				sleep(3);
				checkDateTime(deviceService, &offset);
				setSystemDateAndTime(deviceService, m_username, m_password, offset, "CET-1CEST,M3.5.0,M10.5.0/3", 1);
				sleep(3);
			}
			getDeviceInformation(deviceService, m_username, m_password);
			_tds__GetCapabilitiesResponse response;
			if ( getCapabilities(deviceService, m_username, m_password, response) == SOAP_OK) {
				mediaService= response.Capabilities->Media->XAddr.c_str(); // segfaults on direct std::string = std::string assignment??
				//printf("Mediaservice: %s\n",mediaService.c_str());

				std::map <std::string, std::string> profiles;
				profiles = getProfiles(mediaService, m_username, m_password);
				/* for (std::map <std::string, std::string>::const_iterator it = profiles.begin(); it != profiles.end(); it++) {
					printf("Profile: %s\n", it->first.c_str());
				} */
				std::map <std::string, std::string>::const_iterator it = profiles.find(targetprofile);
				if (it != profiles.end()) { // cam supports wanted profile, get the URI
					printf("URI: %s\n", getRTSPUri(mediaService, m_username, m_password, targetprofile).c_str());
					agoConnection.addDevice(getRTSPUri(mediaService, m_username, m_password, targetprofile).c_str(), "onvifnvt");
					// deleteProfile(mediaService, m_username, m_password, targetprofile);
				} else { // create profile otherwise
					/* it = profiles.begin();
					if (it != profiles.end()) {
					} */
					printf("Profile not found, creating..\n");
					createProfile(mediaService, m_username, m_password);
					printf("URI: %s\n", getRTSPUri(mediaService, m_username, m_password, targetprofile).c_str());
					agoConnection.addDevice(getRTSPUri(mediaService, m_username, m_password, targetprofile).c_str(), "onvifnvt");
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
