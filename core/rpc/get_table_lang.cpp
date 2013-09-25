#include <iostream>
#include <fstream>
#include <string>
#include <stdlib.h>

using namespace std;

int main(int argc, char **argv){
	cout << "Content-Type: text/plain\r\n\r\n";
	std::string querystring = getenv("QUERY_STRING");
	if (querystring.find("/")!=string::npos) return 0;
	if (querystring.find("&")!=string::npos) return 0;
	int pos;
	pos = querystring.find("lang=");
	if (pos==string::npos) return 0;
	std::string lang= querystring.substr(pos+5,querystring.length());
	if (lang.size() != 2) return 0;
	std::string filename = "../datatables_lang/" + lang + ".txt";
	ifstream fin(filename.c_str());
	string line;
	if (fin) {
		while (getline(fin,line)) cout << line << endl;
	} else {
		ifstream fdef("../datatables_lang/en.txt");
		while (getline(fdef,line)) cout << line << endl;
	}
	return 0;
}

