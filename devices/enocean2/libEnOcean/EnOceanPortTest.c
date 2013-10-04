/*
 Copyright 2008 Daniel Lechner, Andreas Dielacher
 see COPYING file for details.
 ============================================================================
 Name        : EnOceanPortTest.c
 Author      : Andreas Dielacher, Daniel Lechner
 Version     : 0.1
 Copyright   : GPL
 Description : Testprogram for the EnOceanPortLibrary
 ============================================================================
*/

#include <signal.h>
#include <stdio.h>
#include <stdlib.h>


#include "EnOceanProtocol.h"
#include "EnOceanPort.h"
#include "TCM120.h"

/** Handler for SIGINT
 **/
void leave(int sig) {
	puts("\nclosing serial port and exiting...\n");
	enocean_cleanup();
    exit(sig);
}

void cb(enocean_data_structure in)
{
	char* hexstr = enocean_gethex(in);
	printf("%s\n",hexstr);
	free(hexstr);

	char* humanstring;
        humanstring = enocean_hexToHuman(in);
        printf("frame is: %s\n",humanstring);
        free(humanstring);

}

/**
 * main? Don't know, what main does ;)
 */
int main(int argc, char *argv[]) {
	enocean_data_structure mydata;
	printf("Testprogram started...\n");

/*
	int testint = sizeof("hallo");
        printf("testint is %d\n",testint);
	enocean_data_structure frame;
	testint = sizeof(frame);
	printf("testint is %d\n",testint);
	frame = enocean_clean_data_structure();
	char* humanstring;
	humanstring = enocean_hexToHuman(frame);
	printf("frame is: %s",humanstring);
	free(humanstring);
*/

/*
	mydata = clean_data_structure();
	mydata.DATA_BYTE3 = 0x97;
	int rid = maskAndShift(mydata.DATA_BYTE3, DB3_RPS_NU_RID, DB3_RPS_NU_RID_SHIFT);
	int ud  = maskAndShift(mydata.DATA_BYTE3, DB3_RPS_NU_UD,  DB3_RPS_NU_UD_SHIFT);
	int pr  = maskAndShift(mydata.DATA_BYTE3, DB3_RPS_NU_PR,  DB3_RPS_NU_PR_SHIFT);
	int srid= maskAndShift(mydata.DATA_BYTE3,DB3_RPS_NU_SRID,DB3_RPS_NU_SRID_SHIFT);
	int sud = maskAndShift(mydata.DATA_BYTE3, DB3_RPS_NU_SUD, DB3_RPS_NU_SUD_SHIFT);
	int sa  = maskAndShift(mydata.DATA_BYTE3, DB3_RPS_NU_SA,  DB3_RPS_NU_SA_SHIFT);

	printf("prüfe daten...\n");
	if (rid != 2)
		printf("RID stimmt nicht!");
	if (ud != 0)
		printf("UD stimmt nicht!");
	if (pr != 1)
		printf("PR stimmt nicht!");
	if (srid != 1)
		printf("SRID stimmt nicht!");
	if (sud != 1)
		printf("SUD stimmt nicht!");
	if (sa != 1)
		printf("SA stimmt nicht!");
	printf("prüfung beendet\n");

*/

	(void) signal(SIGINT,leave);
	mydata = enocean_clean_data_structure();
	mydata = tcm120_rd_idbase();


	enocean_error_structure error = enocean_init("/dev/usbenocean");
	if (error.code != E_OK) {
		printf("%s\n",error.message);
		return EXIT_FAILURE;
	}
	enocean_set_callback_function(cb);
	enocean_send(&mydata);
	puts("waiting...");
	while (1==1) {
		// printhex(mydata);
	}
	enocean_cleanup();
    printf("fertig!!!\n");
	return EXIT_SUCCESS;
}
