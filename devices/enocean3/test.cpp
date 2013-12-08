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
	esp3::sendFrame();
        while (true) {
		esp3::readFrame();
 	}

}
