#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>

#include <signal.h>
#include <pwd.h>
#include <dirent.h>

#include <string>
#include <iostream>

#include "agoclient.h"


using namespace std;
using namespace agocontrol;

qpid::types::Variant::Map pids;
std::list<string> services;

void listServices() {
	
	services.empty();
	// add core services to list
	services.push_back("agoresolver");
	services.push_back("agotimer");
	services.push_back("agorpc");
	services.push_back("agoevent.py");
	services.push_back("agoscenario.py");
	DIR *enabled = opendir("/opt/agocontrol/devices-enabled");
	if (enabled != NULL) {
		while (struct dirent *entry = readdir(enabled)) {
			string path = "/opt/agocontrol/devices-enabled/";
			path += entry->d_name;
			struct stat sb;
			if (lstat(path.c_str(), &sb) != -1) {
				if (S_IFLNK == (sb.st_mode & S_IFMT)) {
					services.push_back(string(entry->d_name));
					// cout << "Enabling device: " << entry->d_name << endl;
				}
			}
		}
		closedir(enabled);
	}

}

string findChild(int pid) {
	for (qpid::types::Variant::Map::const_iterator it = pids.begin(); it != pids.end(); ++it) {
		int tmp = it->second;
		if (tmp == pid) return it->first;
	}
	return "";
}
void signalChild(int arg){
	int pid ;
	int status;
	cout << "SIGCHLD" << endl;
	pid = wait(&status) ;
	if (WIFEXITED(status)) {
		printf("signal's wait() caught pid %d - child %s exit code: %i\n", pid, findChild(pid).c_str(), WEXITSTATUS(status)) ;
	} else if (WIFSIGNALED(status)) {
		printf("signal's wait() caught pid %d - child %s term sig: %i\n", pid, findChild(pid).c_str(), WTERMSIG(status)) ;
	}
	signal(SIGCHLD, signalChild) ;
}

int spawnProcess(const char *path) {
	pid_t pid = fork();
	char *newargv[] = { NULL };
	char *newenviron[] = { NULL };
	
	switch (pid) {
		case -1: 
			std::cerr << "ERROR, can't fork!" << std::endl;
			return -1;
		case 0:
			// child
			execve(path, newargv, newenviron);
			std::cerr << "execve() returned" << std::endl;
			exit(1);
		default:
			//parent
			std::cout << "spawned pid: " << pid << std::endl;
			return pid;
	}
	return -1;
}

std::string commandHandler(qpid::types::Variant::Map content) {
	cout << "command handler" << endl;
	if (content["command"] == "exit" ) {
		exit(0);
	}
	if (content["command"] == "kill" ) {
		int pid = 0;
		pid = pids["agokwikwai"];
		cout << "killing child pid: " << pid << endl;
		kill(pid, SIGKILL);	
	} 
	return "";
}

int main(int argc, char **argv) {

	if (getuid() == 0) {
		std::clog << "running as root, dropping privileges" << std::endl;
		struct passwd *pwstruct;
		pwstruct = getpwnam("agocontrol");
		if (pwstruct == NULL) {
			std::cerr << "ERROR, can't lookup user agocontrol!" << std::endl;
			exit(1);
		}
		if (setgid(pwstruct->pw_gid) != 0) {
			std::cerr << "ERROR, can't drop privileges!" << std::endl;
			exit(1);
		}
		if (setuid(pwstruct->pw_uid) != 0) {
			std::cerr << "ERROR, can't drop privileges!" << std::endl;
			exit(1);
		}
	}

	signal(SIGCHLD, signalChild) ;

	listServices();
	for(std::list<string>::iterator list_iter = services.begin(); 
	    list_iter != services.end(); list_iter++)
	{
		std::cout<< "Starting: " << *list_iter<<endl;
		string service = "/opt/agocontrol/bin/" + *list_iter;
		int pid = spawnProcess(service.c_str());
		pids[*list_iter] = pid;
		sleep(1);
	}
	AgoConnection agoConnection = AgoConnection("agomanager");	
	agoConnection.addDevice("agomanager", "agomanager");
	agoConnection.addHandler(commandHandler);

	agoConnection.run();
//	int status;
//	waitpid(pid, &status, 0);
	cout << "agoman exit" << endl;
}
