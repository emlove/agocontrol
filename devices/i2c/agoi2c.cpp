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
AgoConnection *agoConnection;

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

bool i2cread(const char *device, int i2caddr, int command, size_t size, __u8 &buf) {
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

	int result = i2c_smbus_read_i2c_block_data(file, command, size,&buf);
	printf("result: %d\n",result);

	return true;
}

bool set_pcf8574_output(const char *device, int i2caddr, int output, bool state) {
	unsigned char buf[10];
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

	if (read(file, buf, 1)!= 1) {
		printf("Unable to read from slave\n");
		return false;
	}

	if (!state) {
		buf[0] |= (1 << output);
	} else {
		buf[0] &= ~(1 << output);
	}
	if (write(file, buf, 1) != 1) {
		printf("Error writing to i2c slave\n");
		return false;
	}
	
	return true;
}

bool get_pcf8574_state(const char *device, int i2caddr, uint8_t &state) {
        unsigned char buf[10];
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

        if (read(file, buf, 1)!= 1) {
                printf("Unable to read from slave\n");
                return false;
        }
	state = buf[0];
	return true;
}

qpid::types::Variant::Map commandHandler(qpid::types::Variant::Map content) {
	qpid::types::Variant::Map returnval;
	returnval["result"]=0;
	string internalid = content["internalid"].asString();
	if (internalid.find("pcf8574:") != std::string::npos) {
		unsigned found = internalid.find(":");
		string tmpid = internalid.substr(found+1);
		bool state;
		if (content["command"] == "on") state = true; else state=false;
		unsigned sep = tmpid.find("/");
		if (sep != std::string::npos) {
			int output = atoi(tmpid.substr(sep+1).c_str());
			int i2caddr = strtol(tmpid.substr(0, sep).c_str(), NULL, 16);
			printf("setting i2caddr: 0x%x, output: %i, state: %i\n", i2caddr, output, state); 
			if (set_pcf8574_output(devicefile.c_str(),i2caddr, output, state)) {
				if (state) { 
					agoConnection->emitEvent(internalid.c_str(), "event.device.statechanged", "255", "");
				} else {
					agoConnection->emitEvent(internalid.c_str(), "event.device.statechanged", "0", "");
				}
			} else returnval["result"] = -1;
		}
	}
	return returnval;
}


int main(int argc, char** argv) {
	devicefile=getConfigOption("i2c", "bus", "/dev/i2c-0");
	stringstream devices(getConfigOption("i2c", "devices", "pcf8574:32")); 


	agoConnection = new AgoConnection("i2c");		
	printf("connection to agocontrol established\n");

	string device;
	while (getline(devices, device, ',')) {
		stringstream tmpdevice(device);
		string type;
		getline(tmpdevice, type, ':');
		if (type == "pcf8574") {
			string addr;
			getline(tmpdevice, addr, ':');
			uint8_t state;
			if (get_pcf8574_state(devicefile.c_str(), atoi(addr.c_str()), state)!= true) {
				cout << "Error, can't read state on startup" << endl;
			}
			for (int i=0;i<8;i++) {
				stringstream id;
				id << device << "/" << i;
				agoConnection->addDevice(id.str().c_str(), "switch");
				if (state & (1 << i)) {	
					agoConnection->emitEvent(id.str().c_str(), "event.device.statechanged", "255", "");
				} else {
					agoConnection->emitEvent(id.str().c_str(), "event.device.statechanged", "0", "");
				}
			}
		}
	} 
	agoConnection->addHandler(commandHandler);

	printf("waiting for messages\n");
	agoConnection->run();

	return 0;
}
