#include <iostream>
#include <uuid/uuid.h>
#include <stdlib.h>

#include <unistd.h>
#include <pthread.h>
#include <stdio.h>
#include <stdint.h>


#include "esp3.h"

esp3::ESP3 *myESP3;

int main(int argc, char **argv) {
	myESP3 = new esp3::ESP3("/dev/ttyAMA0");
	myESP3->init();
	std::cout << "ID base: " << myESP3->getIdBase() << std::endl;
	myESP3->fourbsCentralCommandDimLevel(1,0x64,1);
        while (true) {
		sleep(1);
 	}

}
