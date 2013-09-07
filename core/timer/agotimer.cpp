#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>

#include <syslog.h>

#include <cstdlib>
#include <iostream>

#include <sstream>

#include "sunrise.h"
#include "agoclient.h"

using namespace qpid::messaging;
using namespace qpid::types;
using namespace agocontrol;


using std::stringstream;
using std::string;

AgoConnection *agoConnection;

typedef struct { float lat; float lon;} latlon_struct;

void *timer(void *param) {
	time_t now;
	struct tm *tms;
	int waitsec;
	while (1) {
		Variant::Map content;
		now = time(NULL);
		tms = localtime(&now);
		waitsec = 60-tms->tm_sec;
		if (waitsec == 60) {
			// just hit the full minute
			//printf("MINUTE %i:%i\n",tms->tm_min,tms->tm_sec);
		} else {
			sleep(waitsec);
			now = time(NULL);
			tms = localtime(&now);
			// printf("MINUTE %i:%i\n",tms->tm_min,tms->tm_sec);
		}
		content["minute"]=tms->tm_min;
		content["second"]=tms->tm_sec;
		content["hour"]=tms->tm_hour;
		content["month"]=tms->tm_mon+1;
		content["day"]=tms->tm_mday;
		content["year"]=tms->tm_year+1900;
		content["weekday"]=tms->tm_wday;
		content["yday"]=tms->tm_yday;
		agoConnection->sendMessage("event.environment.timechanged", content);
		sleep(2);
	}
}

void *suntimer(void *param) {
	time_t seconds;
	time_t sunrise, sunset,sunrise_tomorrow,sunset_tomorrow;
	latlon_struct *latlon;


	latlon = (latlon_struct*)param;
	float lat = latlon->lat;
	float lon = latlon->lon;

	while(1) {
		Variant::Map content;
		std::string subject;
		seconds = time(NULL);
		if (GetSunriseSunset(sunrise,sunset,sunrise_tomorrow,sunset_tomorrow,lat,lon)) {
			if (seconds < sunrise) {
				// it is night, we're waiting for the sunrise
				subject = "event.environment.sunrise";
				syslog(LOG_NOTICE, "minutes to wait for sunrise: %ld\n",(sunrise-seconds)/60);
				// printf("minutes to wait for sunrise: %ld\n",(sunrise-seconds)/60);
				// printf("sunrise: %s\n",asctime(localtime(&sunrise)));
				sleep(sunrise-seconds);
				syslog(LOG_NOTICE, "sending sunrise event");
			} else if (seconds > sunset) {
				// printf("it is dark\n");
				subject = "event.environment.sunrise";
				syslog(LOG_NOTICE, "minutes to wait for sunrise: %ld\n",(sunrise_tomorrow-seconds)/60);
				sleep(sunrise_tomorrow-seconds);
				syslog(LOG_NOTICE, "sending sunrise event");
			} else {
				subject = "event.environment.sunset";
				syslog(LOG_NOTICE, "minutes to wait for sunset: %ld\n",(sunset-seconds)/60);
				sleep(sunset-seconds);
				syslog(LOG_NOTICE, "sending sunset event");
			}
			agoConnection->sendMessage(subject.c_str(), content);
			sleep(2);
		} else {
			syslog(LOG_CRIT, "ERROR determining sunrise/sunset time");
			sleep(60);
		}
	}
}

int main(int argc, char** argv) {
	latlon_struct latlon;

	openlog(NULL, LOG_PID & LOG_CONS, LOG_DAEMON);

	agoConnection = new AgoConnection("timer");

	latlon.lat=atof(getConfigOption("system", "lat", "47.07").c_str());
	latlon.lon=atof(getConfigOption("system", "lon", "15.42").c_str());

	static pthread_t suntimerThread;
	pthread_create(&suntimerThread,NULL,suntimer,&latlon);

	static pthread_t timerThread;
	pthread_create(&timerThread,NULL,timer,NULL);

	agoConnection->run();	

}


