#include <string>

#include <stdio.h>
#include <unistd.h>

namespace kwikwai {

	class Kwikwai {
		private:
			int write(std::string data);
			std::string read();
			int socketfd;
		public:
			Kwikwai(const char *hostname, const char *port);
			std::string getVersion();
			bool cecSend(const char *command);
	};
}


