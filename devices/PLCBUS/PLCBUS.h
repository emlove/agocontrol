/*
     Copyright (C) 2014 Harald Klein <hari@vt100.at>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

*/
#ifndef PLCBUS_h
#define PLCBUS_h


#include <deque>
#include <map>
#include <algorithm>


// Private member variables
int fd; // file desc for device
static pthread_t readThread;
pthread_mutex_t mutexSendQueue;
struct PLCBUSJob {

	char buffer[1024];
	size_t len;
	time_t timeout;
	int sendcount;
	int usercode;
	int homeunit;
	int command;
	int data1;
	int data2;
};

std::deque < PLCBUSJob *>PLCBUSSendQueue;	

void *receiveFunction(void *param);

#endif
