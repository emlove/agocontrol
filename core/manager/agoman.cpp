#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include <sys/types.h>
#include <sys/wait.h>
#include <sys/stat.h>

#include <fcntl.h>
#include <signal.h>
#include <pwd.h>
#include <dirent.h>
#include <libgen.h>
#include <string.h>

#include <string>
#include <iostream>
#include <cerrno>

#include "agoclient.h"


using namespace std;
using namespace agocontrol;

qpid::types::Variant::Map pids;
qpid::types::Variant::Map pipefds;
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

int spawnProcess(const char *path, int *mypipefd) {
	int pipefd[2];
	char *newargv[] = { NULL };
	char *newenviron[] = { NULL };
	char tmppath[1024];
	strncpy (tmppath, path, 1023);
	tmppath[1023] = 0;
	int flags;

	pipe(pipefd);
	pid_t pid = fork();
		
	switch (pid) {
		case -1: 
			std::cerr << "ERROR, can't fork!" << std::endl;
			return -1;
		case 0:
			// child
			umask(0);
			if (setsid() < 0) {
				std::cerr << "setsid() failed: "<< errno << std::endl;
				exit(1);
			}
			if (chdir(dirname(tmppath)) < 0) std::cerr << "warning, can't chdir(): " << errno << std::endl;
			close(pipefd[0]);
			freopen( "/dev/null", "r", stdin);
			dup2(pipefd[1], 1);
			dup2(pipefd[1], 2);
			close(pipefd[1]);
			execve(path, newargv, newenviron);
			std::cerr << "execve() returned" << std::endl;
			exit(1);
		default:
			//parent
			close(pipefd[1]);
			flags = fcntl(pipefd[0], F_GETFL, 0);
			fcntl(pipefd[0], F_SETFL, flags | O_NONBLOCK);
			*mypipefd = pipefd[0];
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
		int pipefd;
		int pid = spawnProcess(service.c_str(), &pipefd);
		pids[*list_iter] = pid;
		pipefds[*list_iter] = pipefd;
		sleep(1);
	}
	
	while(true) {
		for (qpid::types::Variant::Map::const_iterator it = pipefds.begin(); it != pipefds.end(); ++it) {
			char buffer[1024];
			if (read(it->second, buffer, sizeof(buffer)) != 0) {
				printf("%s", buffer);
			}
		}

	}
	AgoConnection agoConnection = AgoConnection("agomanager");	
	agoConnection.addDevice("agomanager", "agomanager");
	agoConnection.addHandler(commandHandler);
	
	agoConnection.run();
//	int status;
//	waitpid(pid, &status, 0);
	cout << "agoman exit" << endl;
}
