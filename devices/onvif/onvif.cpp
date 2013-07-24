#include <stdio.h>
#include <string>

#include <uuid/uuid.h>

#include "soapStub.h"
#include "RemoteDiscoveryBinding.nsmap"

std::string generateUuid() {
	std::string strUuid;
	char *name;
	if ((name=(char*)malloc(37)) != NULL) {
		uuid_t tmpuuid;
		name[0]=0;
		name[36]=0;
		uuid_generate(tmpuuid);
		uuid_unparse(tmpuuid,name);
		strUuid = std::string(name);
		free(name);
	}
	return strUuid;
}


int main (int argc, char ** argv)  
{  
	struct soap *soap;
	struct wsdd__ProbeType probeType;
	struct __wsdd__ProbeMatches matches;
	struct wsdd__ScopesType scopesType;
	struct SOAP_ENV__Header header;

	char uuid_string[37];
	std::string tmpuuid = "urn:uuid:" +  generateUuid();
	printf("tmpuuid: %s\n", tmpuuid.c_str());
	strncpy (uuid_string, tmpuuid.c_str(), 37);

	soap = soap_new();
	if(soap==NULL) {
		printf("ERROR: Can't initalize soap\n");
		return -1;
	}

	soap_set_namespaces(soap, namespaces);
	soap->recv_timeout=5;

	// set header
	soap_default_SOAP_ENV__Header(soap, &header);
	header.wsa__MessageID = uuid_string;
	header.wsa__To = (char *)"urn:schemas-xmlsoap-org:ws:2005:04:discovery";
	header.wsa__Action = (char *)"http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe";
	soap->header = &header;

	soap_default_wsdd__ScopesType (soap, &scopesType);
	scopesType.__item = (char *)"onvif://www.onvif.org";
	soap_default_wsdd__ProbeType(soap, &probeType);
	probeType.Scopes = &scopesType;

	probeType.Types = "tdn:NetworkVideoTransmitter";

	if (soap_send___wsdd__Probe(soap, "soap.udp://239.255.255.250:3702/", NULL, &probeType) == -1) {
		printf("SOAP error occured: %d %s - %s\n", soap->error, *soap_faultcode(soap), *soap_faultstring(soap));
		return soap->error;
	} else {
		while (soap_recv___wsdd__ProbeMatches(soap, &matches) != -1) {
			printf("match size: %d\n",matches.wsdd__ProbeMatches->__sizeProbeMatch);
			printf("Endpoint Addr: %s\n",matches.wsdd__ProbeMatches->ProbeMatch->wsa__EndpointReference.Address);
			printf("Service Addr: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->XAddrs);
			printf("Type: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->Types);
			printf("Metadata Ver: %d\n",matches.wsdd__ProbeMatches->ProbeMatch->MetadataVersion);
			printf("Scopes Addr: %s\n", matches.wsdd__ProbeMatches->ProbeMatch->Scopes->__item);
		}
	}

} 
