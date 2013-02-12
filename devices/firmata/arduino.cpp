/*
 * Copyright 2008 (c) Scott Reid, dataczar.net
 * $Id$
 * Arduino Microcontroller C++ interface definitions
 * Written for Arduino NG AVR ATmega168
*/

#include <arduino.h>

Arduino::Arduino() {
	fd = -1;
  memset(&term,0,sizeof(termios));
}

Arduino::~Arduino() {
	destroy();
}

int Arduino::destroy() {
  int rv = 0;
	if (fd >= 0) {
		rv = closePort();
	}
	return rv;
}

int Arduino::sendUchar(const unsigned char data) {
#ifdef DEBUG
	printf("Arduino::sendUchar sending: 0x%02x\n",data);
#endif // DEBUG
	if(write(fd, &data, sizeof(char))< 0) {
		perror("Arduino::sendUchar():write():");
		fprintf(stderr,"during write 0x%02x (%c)\n",data,data);
		return(-1);
	}
	return(0);
}
int Arduino::sendString(const string datastr) {
	int rv=0;
	for (unsigned int i=0; i<datastr.size(); i++) {
		unsigned char data = (unsigned char)datastr[i];
#ifdef DEBUG
		printf("Arduino::sendString sending: %01x\n",data);
#endif // DEBUG
		rv |= sendUchar(data);
	}
	return(rv);
}

char* Arduino::getData(double maxWait) {
	memset(serialInBuf,0,ARDUINO_MAX_DATA_BYTES);
	int n=0,eol=0,state=0;
	timeval tv;
	gettimeofday(&tv,NULL);
	double startTime = tv.tv_sec + (float)(tv.tv_usec/1000000.0);
	double elapsed = 0.0;

	while(n < ARDUINO_MAX_DATA_BYTES && ! eol) {
		if (elapsed > maxWait) {
			fprintf(stderr,"Arduino::getData ERROR wait for data %f > maxWait %f\n",elapsed,maxWait);
			return serialInBuf;
		}
		int r;
		if ((r=read(fd,&serialInBuf[n],1)) > 0) {
			if (serialInBuf[n] == '\n') {
				if (state==1) {
					eol = 1;
				}
				else {
					state=1;
				}
			}
			n+=r;
		}
		usleep(100);
		gettimeofday(&tv,NULL);
		double now = tv.tv_sec + (float)(tv.tv_usec/1000000.0);
		elapsed = now - startTime;
	}
	return(serialInBuf);
}

int Arduino::openPort(const char* _serialPort) {
	return(openPort(_serialPort,ARDUINO_DEFAULT_BAUD));
}

int Arduino::openPort(const char* _serialPort, int _baud) {
	strncpy(serialPort,_serialPort,sizeof(serialPort)-1);
	switch(_baud) {
		case 1152000:
			baud=B115200;
			break;
		case 57600:
			baud=B57600;
			break;
		case 38400:
			baud=B38400;
			break;
		case 19200:
			baud=B19200;
			break;
		case 9600:
			baud=B9600;
			break;
		case 4800:
			baud=B4800;
			break;
		case 2400:
			baud=B2400;
			break;
		default:
			baud=B115200;
			break;
	}

	if(fd >= 0) {
		fprintf(stderr,"Connection to %s already open\n",serialPort);
		return(-1);
	}

	printf("Opening connection to Arduino on %s...",serialPort);
	fflush(stdout);

	// Open it. non-blocking at first, in case there's no arduino
	if((fd = open(serialPort, O_RDWR | O_NONBLOCK, S_IRUSR | S_IWUSR )) < 0 ) {
		perror("Arduino::openPort():open():");
		return(-1);
	}
	if(tcflush(fd, TCIFLUSH) < 0) {
		perror("Arduino::openPort():tcflush():");
		close(fd);
		fd = -1;
		return(-1);
	}
	if(tcgetattr(fd, &oldterm) < 0) {
		perror("Arduino::openPort():tcgetattr():");
		close(fd);
		fd = -1;
		return(-1);
	}

	// set up the serial port attributes
	cfmakeraw(&term);
	cfsetispeed(&term, baud);
	cfsetospeed(&term, baud);
	term.c_cflag |= (CLOCAL | CREAD | CS8 );
	term.c_iflag |= ICRNL;

	if(tcsetattr(fd, TCSAFLUSH, &term) < 0) {
		perror("Arduino::openPort():tcsetattr():");
		close(fd);
		fd = -1;
		return(-1);
	}
	/* TODO
	if(storeFirmwareVersion() < 0) {
		perror("Arduino::openPort():storeFirmwareVersion():");
		close(fd);
		fd = -1;
		return(-1);
	}
	*/
  /*
	// OK we have a working connection, set to BLOCK
	if((flags = fcntl(fd, F_GETFL)) < 0) {
		perror("Arduino::openPort():fcntl():");
		close(fd);
		fd = -1;
		return(-1);
	}
	if(fcntl(fd, F_SETFL, flags & ~O_NONBLOCK) < 0) {
		perror("Arduino::openPort():fcntl(NONBLOCK):");
		close(fd);
		fd = -1;
		return(-1);
	}
  */
	printf("Done.\n");

	return(0);
}

int Arduino::closePort() {
	int rv = 0;
	rv |= flushPort();
	if(fd < 0) {
		fprintf(stderr,"Connection to %s already closed\n",serialPort);
		rv |= -1;
	}
	else if(tcsetattr(fd, TCSAFLUSH, &oldterm) < 0) {
		perror("Arduino::closePort():tcsetattr():");
		rv |= -2;
		if (close(fd) < 0) {
			perror("Arduino::closePort():close():");
			rv |= -4;
		}
		else {
			fd = -1;
		}
	}
	return(rv);
}

int Arduino::flushPort() {
	if(tcflush(fd, TCIFLUSH) < 0) {
		perror("Arduino::flushPort():tcflush():");
		return(-1);
	}
	return(0);
}
