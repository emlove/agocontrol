/*
     Copyright (C) 2009 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>
#include <uuid/uuid.h>
#include <stdlib.h>

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>

#include "agoclient.h"

using namespace std;
using namespace agocontrol;

extern "C" {
	#include "libEnOcean/cssl.h"
	#include "libEnOcean/EnOceanProtocol.h"
	#include "libEnOcean/EnOceanPort.h"
	#include "libEnOcean/TCM120.h"
}

AgoConnection *agoConnection;

void serialCallBack(enocean_data_structure in);

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	std::string internalid = content["internalid"].asString();
	returnval["result"] = 0;
	return returnval;
}

int main(int argc, char **argv) {
	std::string devicefile;
	devicefile=getConfigOption("enocean", "device", "/dev/usbenocean");

	AgoConnection _agoConnection = AgoConnection("enocean");
	agoConnection = &_agoConnection;

	printf("connection to agocontrol established\n");

	printf("initalizing EnOcean\n");
	enocean_error_structure error = enocean_init((const char *)devicefile.c_str());
	if (error.code != E_OK) {
		printf("%s\n",error.message);
		return false;
	}
	enocean_set_callback_function(serialCallBack);

	enocean_data_structure frame;
	frame = enocean_clean_data_structure();
	frame = tcm120_reset();

	/* char* humanstring;
	humanstring = enocean_hexToHuman(frame);
	printf("frame is: %s",humanstring);
	free(humanstring); */

	enocean_send(&frame);

	// give the TCM120 time to handle the command
	sleep (1);
	
	printf("get ID Base\n");
	frame = enocean_clean_data_structure();
	frame = tcm120_rd_idbase();

	enocean_send(&frame);

	agoConnection->addHandler(commandHandler);
	agoConnection->run();	
}

void serialCallBack(enocean_data_structure in) {

	long id = (in.ID_BYTE3 << 24) + (in.ID_BYTE2 << 16) + (in.ID_BYTE1 << 8) + in.ID_BYTE0;

	switch(in.ORG) {
		case C_ORG_INF_INIT:
			if (in.DATA_BYTE3 != 0x20) printf("Received INF_INIT %c%c%c%c%c%c%c%c\n",in.DATA_BYTE3,in.DATA_BYTE2,in.DATA_BYTE1,in.DATA_BYTE0,in.ID_BYTE3,in.ID_BYTE2,in.ID_BYTE1,in.ID_BYTE0);
			break;
			;;
		case C_ORG_INF_IDBASE:
			printf("Received INF_IDBASE 0x%02x%02x%02x%02x",in.ID_BYTE3,in.ID_BYTE2,in.ID_BYTE1,in.ID_BYTE0);
			printf("TCM120 Module initialized");
			break;
			;;
		case C_ORG_RPS:
			if (in.STATUS & S_RPS_NU) {
				// NU == 1, N-Message
				printf("Received RPS N-Message Node 0x%08x Rocker ID: %i UD: %i Pressed: %i Second Rocker ID: %i SUD: %i Second Action: %i\n", id,
					(in.DATA_BYTE3 & DB3_RPS_NU_RID) >> DB3_RPS_NU_RID_SHIFT, 
					(in.DATA_BYTE3 & DB3_RPS_NU_UD) >> DB3_RPS_NU_UD_SHIFT, 
					(in.DATA_BYTE3 & DB3_RPS_NU_PR)>>DB3_RPS_NU_PR_SHIFT,
					(in.DATA_BYTE3 & DB3_RPS_NU_SRID)>>DB3_RPS_NU_SRID_SHIFT, 
					(in.DATA_BYTE3 & DB3_RPS_NU_SUD)>>DB3_RPS_NU_SUD_SHIFT,
					(in.DATA_BYTE3 & DB3_RPS_NU_SA)>>DB3_RPS_NU_SA_SHIFT);
				

						// ((in.DATA_BYTE3 & DB3_RPS_NU_UD) >> DB3_RPS_NU_UD_SHIFT) ? "1" : "0")
				
			} else {
				// NU == 0, U-Message
				printf("Received RPS U-Message Node 0x%08x Buttons: %i Pressed: %i\n",id,(in.DATA_BYTE3 & DB3_RPS_BUTTONS) >> DB3_RPS_BUTTONS_SHIFT, (in.DATA_BYTE3 & DB3_RPS_PR)>>DB3_RPS_PR_SHIFT);
			}
			break;
			;;
		case C_ORG_1BS:
			printf("Received 1BS Message Node 0x%08x Value 0x%x",id,in.DATA_BYTE3);
				if (((in.STATUS >> 4) & 7) == 0) { // magnet contact profile, send sensor tripped events
					printf("Sending sensor tripped event from Node 0x%08x",id);
				}

			break;
			;;
		case C_ORG_4BS:
			printf("Received 4BS Message Node 0x%08x",id);
			if ((in.DATA_BYTE0 & 8) == 8) {
				// teach in telegram
				if ((in.DATA_BYTE0 & 128) == 128) {
					// new type
					int profile = in.DATA_BYTE3 >> 2;
					// int type = ((in.DATA_BYTE3 & 3) << 5) + (in.DATA_BYTE2 >> 3);
					// int manufacturer = ((in.DATA_BYTE2 & 7) << 8) + in.DATA_BYTE1;
					switch (profile) {
						case 2:	// Temp sensor
							break;
							;;
						case 4:	// Temp & Hum sensor
							break;
							;;
						case 5:	// pressure
							break;
							;;
						case 6:	// Light sensor
							break;
							;;
						case 7:	// Occupancy
							break;
							;;
						case 8:	// Light, Temp, Occup
							break;
							;;
						case 9:	// gas sensor
							break;
							;;
						case 16:	// room operating panel
							break;
							;;
						case 48:	// digital input
							break;
							;;
						case 56:	// central command
							break;
							;;
						default:
							;;
					}
				}

			} else {
				// regular telegram


			}
			break;
			;;
		default:
			char* humanstring;
			humanstring = enocean_hexToHuman(in);
			printf("Received unhandled frame: %s",humanstring);
			printf("DATA: %s\n",humanstring);
			free(humanstring);
			break;
			;;
	}



}
