/*
     Copyright (C) 2014 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/
#include "PLCBUS.h"

#include <iostream>
#include <sstream>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <termios.h>
#include <stdio.h>

#include "agoclient.h"

using namespace qpid::types;
using namespace std;
using namespace agocontrol;

AgoConnection *agoConnection;

int reprq = 0;
bool announce = false;

int serial_write (int dev,uint8_t pnt[],int len)
{
        int res;

        res = write (dev,pnt,len);
        if (res != len) {
                return (-1);
        }
        tcflush(dev, TCIOFLUSH);

        return (len);
}

int serial_read (int dev,uint8_t pnt[],int len,long timeout)
{
        int bytes = 0;
        int total = 0;
        struct timeval tv;
        fd_set fs;

        while (total < len) {
                FD_ZERO (&fs);
                FD_SET (dev,&fs);
                tv.tv_sec = 0;
                tv.tv_usec = 500000;
                // tv.tv_usec = 100000;
                // bytes = select (FD_SETSIZE,&fs,NULL,NULL,&tv);
                bytes = select (dev+1,&fs,NULL,NULL,&tv);

                // 0 bytes or error
                if( bytes <= 0 )
                {
                       return total;
                }

                bytes = read (dev,pnt+total,len-total);
                total += bytes;
        }
	return total;
}

// commandhandler
qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map command) {
	qpid::types::Variant::Map returnval;
	string addr = command["internalid"].asString();
	int house = addr.substr(0,1).c_str()[0]-65;
	int unit = atoi(addr.substr(1,2).c_str())-1;

	PLCBUSJob *myjob = new PLCBUSJob;
	myjob->sendcount=0;
	myjob->homeunit=(house <<4) + unit;
	myjob->usercode=0;
	myjob->data1=0;
	myjob->data2=0;

	returnval["result"] = 0;

	if (command["command"] == "on") {
		myjob->command=192;
	} else if (command["command"] == "off") {
		myjob->command=193;
	} else if (command["command"] == "setlevel") {
		myjob->command=184;
		myjob->data1 = atoi(command["level"].asString().c_str());
	}

	pthread_mutex_lock (&mutexSendQueue);
	PLCBUSSendQueue.push_back(myjob);
	pthread_mutex_unlock (&mutexSendQueue);
	
	return returnval;
}

void *receiveFunction(void *param) {

	uint8_t buf[1024];
	uint8_t bufr[1024];


	int timer = 0;

	while (1) { 
		timer++;
		for (int i=0;i<1020;i++) {
			bufr[i]=0;
		}
		int len = serial_read(fd, bufr, 9, 6);
				// search for SOF
		if (len > 0) {
			// DCE::LoggerWrapper::GetInstance()->Write(LV_RECEIVE_DATA, DCE::IOUtils::FormatHexAsciiBuffer((const char*)bufr, len,"33").c_str());
			if (len!=9) continue;
		}
		// for (int i=0;i<len;i++) printf("%x\n",bufr[i]);

		int i=0;
		while ((bufr[i] != 0x2) && (i < len)) { 
			i++;
		}
		if (bufr[i] == 0x2) {
			// SOF found
			i++;
			if (bufr[i] == 6) { // found plcbus frame
				int tmpusercode = bufr[i+1];	
				int tmphomeunit = bufr[i+2];	
				int tmpcommand = bufr[i+3];	
				int tmpdata1 = bufr[i+4];	
				int tmpdata2 = bufr[i+5];	
				int rxtxswitch = bufr[i+6];
				if (rxtxswitch & 32) { // received ack
					pthread_mutex_lock (&mutexSendQueue);
					if (PLCBUSSendQueue.size() > 0 ) {
						if (PLCBUSSendQueue.front()->homeunit == tmphomeunit) {
							// LoggerWrapper::GetInstance()->Write(LV_DEBUG,"Response from same id as command on send queue, removing command (sendcount: %i)",PLCBUSSendQueue.front()->sendcount);
							PLCBUSJob *myjob = PLCBUSSendQueue.front();
							PLCBUSSendQueue.pop_front();
							delete myjob;
						}
					}
					pthread_mutex_unlock (&mutexSendQueue);
				} else if (rxtxswitch & 64) { // received ID feedback signal
					pthread_mutex_lock (&mutexSendQueue);
					// LoggerWrapper::GetInstance()->Write(LV_CRITICAL,"Received ID feedback signal for home %c, removing command (sendcount: %i)",65+(tmphomeunit >> 4),PLCBUSSendQueue.front()->sendcount);
					PLCBUSJob *myjob = PLCBUSSendQueue.front();
					PLCBUSSendQueue.pop_front();
					delete myjob;
					pthread_mutex_unlock (&mutexSendQueue);
					for (int i=0;i<8;i++) {
						if (tmpdata2 & 1<<i) {
							// LoggerWrapper::GetInstance()->Write(LV_CRITICAL,"Found Unit %c%i",65+(tmphomeunit >> 4),i+1);
							if (announce) {
								char internalid[20];
								snprintf(internalid, 19, "%c%i", 65+(tmphomeunit >> 4),i+1);
								agoConnection->addDevice("dimmer", internalid);
							}
						}
					}
					for (int i=0;i<8;i++) {
						if (tmpdata1 & 1<<i) {
							// LoggerWrapper::GetInstance()->Write(LV_CRITICAL,"Found Unit %c%i",65+(tmphomeunit >> 4),i+9);
						}
					}
				} else if (rxtxswitch & 0x1c) {
					// received bus copy
					// LoggerWrapper::GetInstance()->Write(LV_DEBUG,"frame seen on bus");
					continue;
				}
	
			}
		} //...

		pthread_mutex_lock (&mutexSendQueue);
		if (PLCBUSSendQueue.size() > 0 ) {
			int commandlength = 8;
			buf[0]=0x2; // STX
			buf[1]=5; // LEN
			buf[2]=PLCBUSSendQueue.front()->usercode; // USERCODE
			buf[3]=PLCBUSSendQueue.front()->homeunit;
			buf[6]=0;
			switch(PLCBUSSendQueue.front()->command) {
				case 192:
					buf[4]=0x02 | 32 | reprq; // ON + ACK_PULSE
					break;
				case 193:
					buf[4]=0x03 | 32 | reprq; // OFF + ACK_PULSE
					break;
				case 184:
					buf[4]=0x0c | 32 | reprq; // PRESETDIM + ACK_PULSE
					buf[6]=0x3; // dim rate
					break;
				case 1:
					buf[4]=0x1c;
					break;
				default:
					buf[4]=0x02 | 32 | reprq;
			}
			buf[5]=PLCBUSSendQueue.front()->data1;
			buf[7]=0x03; // ETX

			// LoggerWrapper::GetInstance()->Write(LV_DEBUG,"Send Queue Size: %i",PLCBUSSendQueue.size());
			// DCE::LoggerWrapper::GetInstance()->Write(LV_SEND_DATA, "Sending job %p - %s",PLCBUSSendQueue.front(),DCE::IOUtils::FormatHexAsciiBuffer((const char*)buf, 8,"31").c_str());

			PLCBUSSendQueue.front()->sendcount++;
			serial_write(fd,(uint8_t*)buf,commandlength);

			if (PLCBUSSendQueue.front()->sendcount > 3) {
				// LoggerWrapper::GetInstance()->Write(LV_CRITICAL,"Sendcount exceeded, this was the last sent attempt, removing job...");
				PLCBUSSendQueue.pop_front();
			}
			// for(int i=0;i<commandlength;i++) {
		 //		printf("0x%x ",(unsigned char) buf[i]);
		 //	}
		 //	printf("\n");
		}
		pthread_mutex_unlock (&mutexSendQueue);

	}
}



int main(int argc, char **argv) {

	if (getConfigOption("PLCBUS", "phases", "3") == "3") {
		reprq = 64;
	}
	if (getConfigOption("PLCBUS", "announce", "no") == "yes") {
		announce = true;
	}


	fd = open(getConfigOption("PLCBUS", "device", "/dev/ttyUSB0").c_str(), O_RDWR);
	// TODO: check for error

	agoConnection = new AgoConnection("PLCBUS");

	agoConnection->addHandler(commandHandler);

	stringstream dimmers(getConfigOption("PLCBUS", "dimmers", "A1"));
	string dimmer;
	while (getline(dimmers, dimmer, ',')) {
		agoConnection->addDevice(dimmer.c_str(), "dimmer");
		cout << "adding code " << dimmer << " as dimmer" << endl;
	} 
	stringstream switches(getConfigOption("PLCBUS", "switches", "A2"));
	string switchdevice;
	while (getline(switches, switchdevice, ',')) {
		agoConnection->addDevice(switchdevice.c_str(), "switch");
		cout << "adding code " << switchdevice << " as switch" << endl;
	} 
	
	// B9600 8n1
	struct termios tio;
	tcgetattr(fd, &tio);
	tio.c_cflag = CS8 | CLOCAL | CREAD;
	tio.c_cc[VMIN] = 1;
	tio.c_cc[VTIME] = 0;
	tio.c_lflag = 0;
	tio.c_iflag = IGNBRK;
	tio.c_oflag = 0;
	cfsetispeed(&tio, B9600);
	cfsetospeed(&tio, B9600);
	tcflush(fd, TCIFLUSH);
	tcsetattr(fd,TCSANOW,&tio);

	pthread_mutex_init(&mutexSendQueue, NULL);
	static pthread_t readThread;
	pthread_create(&readThread, NULL, receiveFunction, NULL);

	for (int i=0;i<5;i++) {
		PLCBUSJob *myjob = new PLCBUSJob;
		myjob->sendcount=0;
		myjob->homeunit=(i <<4);
		myjob->usercode=0;
		myjob->data1=0;
		myjob->data2=0;
		myjob->command=1;
		// LoggerWrapper::GetInstance()->Write(LV_DEBUG,"Adding get all ID command to queue...");
		pthread_mutex_lock (&mutexSendQueue);
		PLCBUSSendQueue.push_back(myjob);
		pthread_mutex_unlock (&mutexSendQueue);
	}

	agoConnection->run();

}


