/*
 Copyright 2008 Daniel Lechner, Andreas Dielacher
 see COPYING and COPYING.LESSER file for details.
*/
#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <string.h>

#include "cssl.h"
#include "EnOceanPort.h"
#include "TCM120.h"


int nQueueID;

cssl_t *serial;

static enocean_data_structure receivebuffer[BUFSIZE]; ///< the buffer for received dataframes
static int frames_received = 0; ///< The actual dataframe being received (=write position) - ringbuffer -> modulo BUFSIZE
static int bytes_received = 0; ///< the position in the actual (receiving) frame
static int frames_read = 0; ///< some variable for read-position

static callback_func callback = NULL;


/**
 * Do cleanup like close ports, free memory, ...
 */
void enocean_cleanup() {
    cssl_close(serial);
    cssl_stop();
/*    if (msgctl(nQueueID, IPC_RMID, NULL) == -1) {
    	puts("Cannot remove message queue!");
    }
*/
}

/**
 * Print out the passed datastructure in hexadecimal format
 * @param in the data structure that is going to be print
**/
void enocean_printhex(enocean_data_structure in) {
	int i;
	BYTE* bytearray = (BYTE*)&in;
	for (i=0;i<sizeof(in);i++) {
		printf("%02x",bytearray[i]);
	}
}

char* enocean_gethex_internal(BYTE* in, const int framesize) {
	char* hexstr = (char*) malloc ((framesize*2)+1);  // because every hex-byte needs 2 characters
	char* tempstr = hexstr;

	int i;
	BYTE* bytearray;
	bytearray = in;
	for (i=0;i<framesize;i++) {
		sprintf(tempstr,"%02x",bytearray[i]);
		tempstr += 2;
	}
	return hexstr;
}

char* enocean_gethex(enocean_data_structure in) {
	const int framesize = sizeof(in);
	return (char*)enocean_gethex_internal((BYTE*)&in, framesize);
}

char* enocean_gethex_byte(BYTE in) {
	const int framesize = sizeof(in);
	return (char*)enocean_gethex_internal(&in, framesize);
}

/** Is called, if a full frame was received
 */
void frame_receive() {
	if(callback != NULL)
		callback(receivebuffer[frames_read]);
//	printf("received frame %d: ", frames_read);
//	printhex(receivebuffer[frames_read]);
//	printf("\n");
	frames_read++;
	frames_read%=BUFSIZE;
}

/** Is called, when some byte was received (only for internal use!)
 */
static void raw_receive(int id, uint8_t *buf, int length) {
    int i;
    for(i=0;i<length;i++) {
    	// write received byte into buffer
    	BYTE* actual_frame = (BYTE*) &(receivebuffer[frames_received]);
    	*(actual_frame + bytes_received*sizeof(BYTE)) = buf[i];
    	bytes_received++;
    	if (bytes_received >= (sizeof(struct enocean_data_structure)/sizeof(BYTE))) {
    		// data-frame full -> begin next one and call appropirate function
    		bytes_received = 0;
    		frames_received++;
    		frames_received%=BUFSIZE;
    		frame_receive();
    	}
    }
}

/**
 * returns a clean data structure, filled with 0
 */
enocean_data_structure enocean_clean_data_structure() {
	int i = 0;
	enocean_data_structure ds;
	BYTE* b;
	for (i=0;i < sizeof(ds);i++) {
		b = (BYTE*) &ds + i;
		*b = 0x00;
	}
	return ds;
}

/**
 * Convert a data_structure into a data_structure_6DT
 * Note: There will be no copy of the passed data_structure.
 *   So if you change data in the returned new structure, also
 *   data in the original struct will be changed (pointers!)
 */
enocean_data_structure_6DT* enocean_convert_to_6DT(enocean_data_structure* in) {
	enocean_data_structure_6DT* out;
	// no conversion necessary - just overlay the other struct
	out = (enocean_data_structure_6DT*) in;
	return out;
}

/**
 * Convert a data_structure into a data_structure_MDA
 * Note: There will be no copy of the passed data_structure.
 *   So if you change data in the returned new structure, also
 *   data in the original struct will be changed (pointers!)
 */
enocean_data_structure_MDA* enocean_convert_to_MDA(enocean_data_structure* in) {
	enocean_data_structure_MDA* out;
	// no conversion necessary - just overlay the other struct
	out = (enocean_data_structure_MDA*) in;
	return out;
}

BYTE enocean_calc_checksum(enocean_data_structure input_data) {
  BYTE checksum = 0;
  checksum += input_data.H_SEQ_LENGTH;
  checksum += input_data.ORG;
  checksum += input_data.DATA_BYTE3;
  checksum += input_data.DATA_BYTE2;
  checksum += input_data.DATA_BYTE1;
  checksum += input_data.DATA_BYTE0;
  checksum += input_data.ID_BYTE3;
  checksum += input_data.ID_BYTE2;
  checksum += input_data.ID_BYTE1;
  checksum += input_data.ID_BYTE0;
  checksum += input_data.STATUS;
  return checksum;
}

int enocean_maskAndShift(BYTE data, BYTE mask, int shifts) {
	BYTE returnvalue = data;
	returnvalue &= mask;
	returnvalue >>= shifts;
	return returnvalue;
}

enocean_error_structure enocean_init(const char* devicefile) {
	enocean_error_structure es;
	es.code = E_OK;
	es.message = "";
	cssl_start();
	// 9600 bps, 8 data, 0 parity, 1 stop)
	serial=cssl_open(devicefile,raw_receive,0,9600,8,0,1);
	if (!serial) {
		es.code = E_DEVICE_OPEN_FAILURE;
		es.message = cssl_geterrormsg();
	}
	return es;
}

void enocean_send_raw(BYTE* data, int size)
{

	cssl_putdata(serial,(uint8_t*)data,size);
}

void enocean_send(enocean_data_structure* data)
{
	enocean_send_raw((BYTE*)data, sizeof(*data));
}

void enocean_send_byte(BYTE* data)
{
	enocean_send_raw((BYTE*)data, sizeof(*data));
}

void enocean_set_callback_function(callback_func the_function)
{
	callback = the_function;
}

// NOTE: This is not my (daniel) code. So there might be some "strange" things inside. If I have time, I will have a look
char* enocean_hexToHuman(enocean_data_structure frame)
{
	// Code vom Andi, bitte nicht töten wie der ausschaut :)
	const int framesize = sizeof(frame);
	// every byte of the frame takes 2 characters in the human representation + the length of the text blocks (without trailing '\0');
	const int stringsize = (framesize*2)+1+sizeof(HR_TYPE)-1+sizeof(HR_RPS)-1+sizeof(HR_DATA)-1+sizeof(HR_SENDER)-1+sizeof(HR_STATUS)-1+sizeof(HR_CHECKSUM)-1;
	char *humanString = (char*) malloc (stringsize);
	char *tempstring = humanString;
	char *temphexstring;
	sprintf(tempstring,HR_TYPE);
	tempstring += sizeof(HR_TYPE)-1;

	enocean_data_structure_6DT* frame_6DT;
	enocean_data_structure_MDA* frame_MDA;

	// Now it depends on ORG what to do
	switch (frame.ORG) {
	  case C_ORG_RPS: // RBS received
	  case C_ORG_4BS:
	  case C_ORG_1BS:
	  case C_ORG_HRC:
			switch (frame.ORG) {
			  case C_ORG_RPS: // RBS received
				    sprintf(tempstring,HR_RPS);
				    tempstring += sizeof(HR_RPS)-1;
				    break;
			  case C_ORG_4BS:
				    sprintf(tempstring,HR_4BS);
				    tempstring += sizeof(HR_4BS)-1;
				    break;
			  case C_ORG_1BS:
				    sprintf(tempstring,HR_1BS);
				    tempstring += sizeof(HR_1BS)-1;
				    break;
			  case C_ORG_HRC:
				    sprintf(tempstring,HR_HRC);
				    tempstring += sizeof(HR_HRC)-1;
				    break;
			}
		sprintf(tempstring,HR_SENDER);
		tempstring += sizeof(HR_SENDER)-1;
		temphexstring = enocean_gethex_internal((BYTE*)&(frame.ID_BYTE3), 4);
		(void*)strcpy(tempstring,temphexstring);
		free(temphexstring);
		tempstring += 8;  // we converted 4 bytes and each one takes 2 chars
		sprintf(tempstring,HR_DATA);
		tempstring += sizeof(HR_DATA)-1;
		temphexstring = enocean_gethex_internal((BYTE*)&(frame.DATA_BYTE3), 4);
		(void*)strcpy(tempstring,temphexstring);
		free(temphexstring);
		tempstring += 8;  // we converted 4 bytes and each one takes 2 chars
	    break;
	  case C_ORG_6DT:
		    sprintf(tempstring,HR_6DT);
		    frame_6DT = enocean_convert_to_6DT(&frame);
		    tempstring += sizeof(HR_6DT)-1;
			sprintf(tempstring,HR_SENDER);
			tempstring += sizeof(HR_SENDER)-1;
			temphexstring = enocean_gethex_internal((BYTE*)&(frame_6DT->ADDRESS1), 2);
			(void*)strcpy(tempstring,temphexstring);
			free(temphexstring);
			tempstring += 4;
			sprintf(tempstring,HR_DATA);
			tempstring += sizeof(HR_DATA)-1;
			temphexstring = enocean_gethex_internal((BYTE*)&(frame_6DT->DATA_BYTE5), 6);
			(void*)strcpy(tempstring,temphexstring);
			free(temphexstring);
			tempstring += 12;
		    break;
	  case C_ORG_MDA:
		    sprintf(tempstring,HR_MDA);
		    frame_MDA = enocean_convert_to_MDA(&frame);
		    tempstring += sizeof(HR_MDA)-1;
			sprintf(tempstring,HR_SENDER);
			tempstring += sizeof(HR_SENDER)-1;
			temphexstring = enocean_gethex_internal((BYTE*)&(frame_MDA->ADDRESS1), 2);
			(void*)strcpy(tempstring,temphexstring);
			free(temphexstring);
			tempstring += 4;
		    break;
	  default:
            sprintf(tempstring,HR_TYPEUNKN);
            tempstring += sizeof(HR_TYPEUNKN)-1;
            break;
	}
	sprintf(tempstring,HR_STATUS);
	tempstring += sizeof(HR_STATUS)-1;
	temphexstring = enocean_gethex_internal((BYTE*)&(frame.STATUS), 1);
	(void*)strcpy(tempstring,temphexstring);
	free(temphexstring);
	tempstring += 2;

	sprintf(tempstring,HR_CHECKSUM);
	tempstring += sizeof(HR_CHECKSUM)-1;
	temphexstring = enocean_gethex_internal((BYTE*)&(frame.CHECKSUM), 1);
	(void*)strcpy(tempstring,temphexstring);
	free(temphexstring);
	tempstring += 2;
	return humanString;
}

