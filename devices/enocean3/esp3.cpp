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

size_t readbuf(int fd, uint8_t *buf, size_t size) {
	size_t _size = 0;

	do {
		int numread = read(fd, buf+_size, size - _size);
		if (numread == -1) {
			cerr << "ERROR: can't read from device: " << errno << " - " << strerror(errno) << endl;
			return -1;
		}
		_size += numread;
	} while ( _size < size);
	return _size;
}


bool esp3::init(std::string devicefile) {
	fd = open(devicefile.c_str(), O_RDWR);
	struct termios tio;
	if (tcgetattr(fd, &tio) != 0) {

		cout << "Error " << errno << " from tcgetattr: " << strerror(errno) << endl;
		return false;
	}
	cfsetispeed(&tio, B57600);
	cfsetospeed(&tio, B57600);

	tio.c_cflag     &=  ~PARENB;        // Make 8n1
	tio.c_cflag     &=  ~CSTOPB;
	tio.c_cflag     &=  ~CSIZE;
	tio.c_cflag     |=  CS8;
	tio.c_cflag     &=  ~CRTSCTS;       // no flow control
	tio.c_lflag     =   0;          // no signaling chars, no echo, no canonical processing
	tio.c_oflag     =   0;                  // no remapping, no delays
//	tio.c_cc[VMIN]      =   0;                  // read doesn't block
//	tio.c_cc[VTIME]     =   5;                  // 0.5 seconds read timeout	

	tcflush(fd, TCIFLUSH);
	tcsetattr(fd,TCSANOW,&tio);
	return true;
}

RETURN_TYPE parse_radio(uint8_t *buf, size_t len, size_t optlen) {
	if (len <1) return ADDR_OUT_OF_MEM;
	if (buf == NULL) return ADDR_OUT_OF_MEM;
	for (uint32_t i=0;i<len+optlen;i++) {
		printf("%02x",buf[i]);
	}
	cout << endl;
	if (optlen == 7) {
		printf("destination: 0x%02x%02x%02x%02x\n",buf[len+1],buf[len+2],buf[len+3],buf[len+4]);
		printf("RSSI: %i\n",buf[len+5]);
	} else {
		cout << "Optional data size:" << optlen << endl;
	}
	switch (buf[0]) {
		case RORG_4BS: // 4 byte communication
			cout << "4BS data" << endl;
			break;
		case RORG_RPS: // repeated switch communication
			cout << "RPS data" << endl;
			printf("Sender id: 0x%02x%02x%02x%02x Status: %02x Data: %02x\n",buf[2],buf[3],buf[4],buf[5],buf[6],buf[1]);
			if (buf[6] & (1 << 2)) cout << "T21" << endl;
			break;	
		default:
			printf("WARNING: Unhandled RORG: %02x\n",buf[0]);
			break;
	}
	return OK;
}


bool esp3::readFrame() {
	uint8_t buf[65536];
	size_t len =0;
	uint32_t packetsize =0;
	uint32_t datasize =0 ;
	uint32_t optionaldatasize =0 ;
	uint8_t crc = 0;

	cout << "reading frame" << endl;
	do { // search for the sync code
		readbuf(fd,buf,1);
	} while (buf[0] != SER_SYNCH_CODE);

	len = readbuf(fd,buf+1,5); // read 
	if (len == -1 || len != 5) {
		cerr << "ERROR: can't read size" << endl;
		return -1;
	}

	crc = proc_crc8(crc, buf[1]);
	crc = proc_crc8(crc, buf[2]);
	crc = proc_crc8(crc, buf[3]);
	crc = proc_crc8(crc, buf[4]);
	if (crc != buf[5]) {
		cout << "ERROR: header crc checksum invalid!" << endl;
		cout << "crc: " << crc << " buf[5]: " << buf[5] << endl;
		return -1;
	}

	datasize = (( (uint32_t) buf[1])<<8) + buf[2];
	optionaldatasize = buf[3];
	packetsize = ESP3_HEADER_LENGTH + datasize + optionaldatasize + 3; // 1byte sync, 2byte for two crc8

	len = readbuf(fd, buf+6, datasize+optionaldatasize+1);
	if (len == -1 || len != datasize+optionaldatasize+1) {
		cerr << "ERROR: datasize invalid" << endl;
		return -1;
	}

	crc = 0;
	for (uint32_t i=6;i<datasize+optionaldatasize+6;i++) {
		crc = proc_crc8(crc, buf[i]);
	}
	if (crc != buf[packetsize-1]) {
		cout << "ERROR: data crc checksum invalid!" << endl;
		cout << "crc: " << crc << " buf[packetsize-1]: " << buf[packetsize-1] << endl;
		return -1;
	}

	switch (buf[4]) {
		case PACKET_RADIO:
			cout << "RADIO Frame" << endl;
			parse_radio(buf+6,datasize,optionaldatasize);
			break;
		case PACKET_RESPONSE:
			cout << "RESPONSE Frame" << endl;
			break;
		case PACKET_RADIO_SUB_TEL:
			cout << "RADIO_SUB_TEL Frame" << endl;
			break;
		case PACKET_EVENT:
			cout << "EVENT Frame" << endl;
			break;
		case PACKET_COMMON_COMMAND:
			cout << "COMMON_COMMAND Frame" << endl;
			break;
		case PACKET_SMART_ACK_COMMAND:
			cout << "SMART_ACK_COMMAND Frame" << endl;
			break;
		case PACKET_REMOTE_MAN_COMMAND:
			cout << "REMOTE_MAN_COMMAND Frame" << endl;
			break;
		default:
			cout << "Unknown frame type" << endl;
			break;
	}
	return true;
}
