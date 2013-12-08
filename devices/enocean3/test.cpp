#include <iostream>
#include <uuid/uuid.h>
#include <stdlib.h>

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>
#include <stdint.h>


#include "esp3.h"


int main(int argc, char **argv) {
       esp3::init("/dev/ttyAMA0");
	esp3::readIdBase();
		int len, optlen;
		uint8_t buf[65535];
		// teach in: 0xa5 + [ 0x02 0x00 0x00 0x00 ] + sender + 0x30
		buf[0]=0xa5;
		buf[1]=0x2;
		buf[2]=0x64;
		buf[3]=0x6;
		buf[4]=0x09;
		buf[5]=0xff;
		buf[6]=0x8a;
		buf[7]=0x2a;
		buf[8]=0x01;
		buf[9]=0x30;
		esp3::sendFrame(esp3::PACKET_RADIO, buf, 10, NULL, 0);		
        while (true) {
		uint8_t buf2[65535];
		esp3::readFrame(buf2, len, optlen);
		esp3::parseFrame(buf2, len, optlen);
 	}

}
