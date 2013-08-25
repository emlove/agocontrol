/*
     Copyright (C) 2009 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/

#include <iostream>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>

#include <termios.h>
#include <stdio.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#include "agoclient.h"


using namespace std;
using namespace agocontrol;

int fd; // file desc for device
unsigned short   usp_crc; // initialise per packet with $FFFF.
int increment;
int speed;

void process_crc(unsigned char ucData) {
      int i;
      usp_crc^=ucData;
      for(i=0;i<8;i++){ // Process each Bit
             if(usp_crc&1){ usp_crc >>=1; usp_crc^=0xA001;}
             else{          usp_crc >>=1; }
      }

}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	int red = 0;
	int green = 0;
	int blue = 0;
	unsigned char buf[1024];

	int level = 0;
	if (content["command"] == "on" ) {
		red = 255; green = 255; blue=255;
	} else if (content["command"] == "off") {
		red = 0; green = 0; blue=0;
	} else if (content["command"] == "setlevel") {
		level = content["level"];
		red = green = blue = (int) ( 255.0 * level / 100 );
	} else if (content["command"] == "setcolor") {
		red = content["red"];		
		green = content["green"];		
		blue = content["blue"];		
	}

	// assemble frame
	buf[0]=0xca; // preamble
	buf[1]=0x00; // broadcast
	buf[2]=0x00; // broadcast
	buf[3]=0x00; // broadcast
	buf[4]=0x00; // length 
	buf[5]=0x08; // length
	buf[6]=0x7e; // 7e == effect color
	buf[7]=0x04; // register addr
	buf[8]=red; // R
	buf[9]=green; // G
	buf[10]=blue; // B
	buf[11]=0x00; // X
	buf[12]=increment; // reg 8 - red increment
	buf[13]=increment; // reg 9 - green increment
	buf[14]=increment; // reg 10 - blue increment

	// calc crc16
	usp_crc = 0xffff;
	for (int i = 0; i < 15; i++) process_crc(buf[i]);

	buf[15] = (usp_crc >> 8);
	buf[16] = (usp_crc & 0xff);

	printf("sending command...\n");
	if (write (fd, buf, 17) != 17) {
		printf ("Write error: %s", strerror(errno ));
		returnval["result"] = -1;
	} else {
		returnval["result"] = 0;
	}
	return returnval;
}


int main(int argc, char **argv) {
	string devicefile=getConfigOption("chromoflex", "device", "/dev/ttyS_01");

	fd = open(devicefile.c_str(), O_RDWR);
	unsigned char buf[1024];

	increment=1;
	speed=1;

	// init crc
	usp_crc = 0xffff;

	// disable any programs on the units
	buf[0]=0xca; // preamble
	buf[1]=0x00; // broadcast
	buf[2]=0x00; // broadcast
	buf[3]=0x00; // broadcast
	buf[4]=0x00; // length 
	buf[5]=0x02; // length
	buf[6]=0x7e; // 7e == write register
	buf[7]=18; // register addr
	buf[8]=0x01; // disable internal programs
	for (int i = 0; i < 9; i++) process_crc(buf[i]);
	buf[9] = (usp_crc >> 8);
	buf[10] = (usp_crc & 0xff);

	// setup B9600 8N1 first
	struct termios tio;
	tcgetattr(fd, &tio);
	tio.c_cflag = B9600 | CS8 | CLOCAL | CREAD;
	tcflush(fd, TCIFLUSH);
	tcsetattr(fd,TCSANOW,&tio);

	if (write (fd, buf, 11) != 11) {
		printf("ERROR: can't open device %s:%i\n",devicefile.c_str(),fd);
		exit (1);
	}

	AgoConnection agoConnection = AgoConnection("chromoflex");		
	printf("connection to agocontrol established\n");

	agoConnection.addDevice("0", "dimerrgb");
	agoConnection.addHandler(commandHandler);

	printf("waiting for messages\n");
	agoConnection.run();

	close(fd);
}


