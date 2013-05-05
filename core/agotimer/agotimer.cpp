#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <pthread.h>

#include <syslog.h>

#include <qpid/messaging/Connection.h>
#include <qpid/messaging/Message.h>
#include <qpid/messaging/Sender.h>
#include <qpid/messaging/Session.h>

#include <cstdlib>
#include <iostream>

#include <sstream>

#include "../../shared/CDataFile.h"
#include "sunrise.h"

using namespace qpid::messaging;
using namespace qpid::types;

using std::stringstream;
using std::string;

typedef struct { float lat; float lon; Connection conn;} latlon_struct;

void *suntimer(void *param) {
	time_t seconds;
	time_t sunrise, sunset,sunrise_tomorrow,sunset_tomorrow;
	latlon_struct *latlon;


	latlon = (latlon_struct*)param;
	float lat = latlon->lat;
	float lon = latlon->lon;

	Session session = latlon->conn.createSession();
	Sender sender = session.createSender("agocontrol; {create: always, node: {type: topic}}");

	while(1) {
		Message message;
		Variant::Map content;
		seconds = time(NULL);
		if (GetSunriseSunset(sunrise,sunset,sunrise_tomorrow,sunset_tomorrow,lat,lon)) {
			if (seconds < sunrise) {
				// it is night, we're waiting for the sunrise
				message.setSubject("event.environment.sunrise");
				syslog(LOG_NOTICE, "minutes to wait for sunrise: %ld\n",(sunrise-seconds)/60);
				// printf("minutes to wait for sunrise: %ld\n",(sunrise-seconds)/60);
				// printf("sunrise: %s\n",asctime(localtime(&sunrise)));
				sleep(sunrise-seconds);
				syslog(LOG_NOTICE, "sending sunrise event");
			} else if (seconds > sunset) {
				// printf("it is dark\n");
				message.setSubject("event.environment.sunrise");
				syslog(LOG_NOTICE, "minutes to wait for sunrise: %ld\n",(sunrise_tomorrow-seconds)/60);
				sleep(sunrise_tomorrow-seconds);
				syslog(LOG_NOTICE, "sending sunrise event");
			} else {
				message.setSubject("event.environment.sunset");
				syslog(LOG_NOTICE, "minutes to wait for sunset: %ld\n",(sunset-seconds)/60);
				sleep(sunset-seconds);
				syslog(LOG_NOTICE, "sending sunset event");
			}
			try {
				sender.send(message, true);	
			} catch(const std::exception& error) {
				syslog(LOG_CRIT, "ERROR, raising exception: %s",error.what());
				// std::cout << error.what() << std::endl;
			}
			sleep(2);
		} else {
			syslog(LOG_CRIT, "ERROR determining sunrise/sunset time");
			sleep(60);
		}
	}
}

int main(int argc, char** argv) {
	latlon_struct latlon;
	time_t now;
	struct tm *tms;
	int waitsec;

	openlog(NULL, LOG_PID & LOG_CONS, LOG_DAEMON);
        std::string broker;
        Variant::Map connectionOptions;
        CDataFile ExistingDF("/etc/opt/agocontrol/config.ini");

        t_Str szBroker  = t_Str("");
        szBroker = ExistingDF.GetString("broker", "system");
        if ( szBroker.size() == 0 )
                broker="localhost:5672";
        else
                broker= szBroker;

        t_Str szUsername  = t_Str("");
        szUsername = ExistingDF.GetString("username", "system");
        if ( szUsername.size() == 0 )
                connectionOptions["username"]="agocontrol";
        else
                connectionOptions["username"] = szUsername;

        t_Str szPassword  = t_Str("");
        szPassword = ExistingDF.GetString("password", "system");
        if ( szPassword.size() == 0 )
                connectionOptions["password"]="letmein";
        else
                connectionOptions["password"]=szPassword;

        t_Str szLatitude  = t_Str("");
        szLatitude = ExistingDF.GetString("lat", "system");
        if ( szLatitude.size() == 0 )
		latlon.lat=47.07;
        else
                latlon.lat = atof(szLatitude.c_str());

        t_Str szLongitude  = t_Str("");
        szLongitude = ExistingDF.GetString("lon", "system");
        if ( szLongitude.size() == 0 )
		latlon.lon=15.42;
        else
                latlon.lon=atof(szLongitude.c_str());


        connectionOptions["reconnect"] = "true";

        Connection connection(broker, connectionOptions);
        try {
		connection.open();
		latlon.conn = connection;
		Session session = connection.createSession();
		Sender sender = session.createSender("agocontrol; {create: always, node: {type: topic}}");

		static pthread_t suntimerThread;
		pthread_create(&suntimerThread,NULL,suntimer,&latlon);

		while (1) {
			Message message;
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
			encode(content, message);
			message.setSubject("event.environment.timechanged");
			sender.send(message, true);
			sleep(2);
		}
	} catch(const std::exception& error) {
		syslog(LOG_CRIT, "ERROR, raising exception: %s",error.what());
		std::cout << error.what() << std::endl;
		connection.close();
	}
	connection.close();
}
