#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <iostream>

#include "mongoose.h"

using namespace std;

int main(int argc, char **argv) {
	if (argc != 5) {
		cout << "Usage: " <<  argv[0] << " <filename> <domainname> <username> <password>" << endl;
		exit(-1);
	}
	mg_modify_passwords_file(argv[1], argv[2], argv[3], argv[4]);

}
