#include <stdio.h>
#include <unistd.h>
#include <iostream>
#include <stdlib.h>
#include <sstream>
#include <fcntl.h>

#include <sys/ioctl.h>
#include <linux/i2c-dev.h>

#include "agoclient.h"

using namespace std;
using namespace agocontrol;

string devicefile;

bool i2ccommand(const char *device, int i2caddr, int command, size_t size, __u8  *buf) {
	int file = open(device, O_RDWR);
	if (file < 0) {
		printf("open %s: error = %d\n", device, file);
		return false;
	}
	else
		printf("open %s: succeeded.\n", device);

	if (ioctl(file, I2C_SLAVE, i2caddr) < 0) {
		printf("open i2c slave 0x%02x: error = %s\n\n", i2caddr, "dunno");
		return false;
	}
	else
		printf("open i2c slave 0x%02x: succeeded.\n\n", i2caddr);
	int result = i2c_smbus_write_i2c_block_data(file, command, size,buf);
	printf("result: %d\n",result);

	return true;
}

qpid::types::Variant::Map  commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	int i2caddr = atoi(content["internalid"].asString().c_str());
	__u8 buf[10];
	// TODO: send proper status events
	if (content["command"] == "on" ) {
		buf[0]=0xff;
		buf[1]=0xff;
		buf[2]=0xff;
		i2ccommand(devicefile.c_str(),i2caddr,0x63,3,buf); // stop script on blinkm
	} else if (content["command"] == "off") {
		buf[0]=0x0;
		buf[1]=0x0;
		buf[2]=0x0;
		i2ccommand(devicefile.c_str(),i2caddr,0x63,3,buf); // stop script on blinkm
	} else if (content["command"] == "setlevel") {
		buf[0] = atoi(content["level"].asString().c_str()) * 255 / 100;
		buf[1] = atoi(content["level"].asString().c_str()) * 255 / 100;
		buf[2] = atoi(content["level"].asString().c_str()) * 255 / 100;
		i2ccommand(devicefile.c_str(),i2caddr,0x63,3,buf); // stop script on blinkm
	} else if (content["command"] == "setcolor") {
		int red = 0;
		int green = 0;
		int blue = 0;
		red = content["red"];
		green = content["green"];
		blue = content["blue"];
		buf[0] = red * 255 / 100;
		buf[1] = green * 255 / 100;
		buf[2] = blue * 255 / 100;
		i2ccommand(devicefile.c_str(),i2caddr,0x63,3,buf); // stop script on blinkm
	}
	// TODO: determine proper result code
	returnval["result"] = 0;
	return returnval;
}


int main(int argc, char** argv) {
	devicefile=getConfigOption("blinkm", "bus", "/dev/i2c-0");
	stringstream devices(getConfigOption("blinkm", "devices", "9")); // read blinkm addr from config, default to addr 9


	AgoConnection agoConnection = AgoConnection("blinkm");		
	printf("connection to agocontrol established\n");

	string device;
	while (getline(devices, device, ',')) {
		agoConnection.addDevice(device.c_str(), "dimmerrgb");
		i2ccommand(devicefile.c_str(),atoi(device.c_str()),0x6f,0,NULL); // stop script on blinkm
	} 
	agoConnection.addHandler(commandHandler);

	printf("waiting for messages\n");
	agoConnection.run();

	return 0;
}
