#include <iostream>
#include <stdlib.h>
#include <unistd.h>
#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <string.h>
#include <termios.h>
#include <errno.h>

#include "esp3.h"

using namespace esp3;
using namespace std;

int fd;

bool esp3::init(std::string devicefile) {
	fd = open(devicefile.c_str(), O_RDWR);
	struct termios tio;
	tcgetattr(fd, &tio);
	tio.c_cflag = B57600 | CS8 | CLOCAL | CREAD;
	tcflush(fd, TCIFLUSH);
	tcsetattr(fd,TCSANOW,&tio);
}

size_t esp3::readFrame(uint8_t *buffer) {
	uint8_t buf[1024];
	do {
		if (read(fd,buf,1) == -1) {
			cerr << "ERROR: can't read from device:" << strerror(errno) << endl;
			return -1;
		}

	} while (buf[0] != SER_SYNCH_CODE);
	cout << "frame found" << endl;	

}

RETURN_TYPE esp3::parseFrame(uint8_t *buffer, size_t size) {



	return OK;
}
