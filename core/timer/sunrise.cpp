#include <stdio.h>
#include <iostream>
#include <time.h>

#include <hdate.h>

bool GetSunriseSunset(time_t &tSunrise,time_t &tSunset,time_t &tSunriseTomorrow,time_t &tSunsetTomorrow,float latitude,float longitude)
{
	tzset();
	time_t rawtime;
	tm ptm;
	int sunrise = 0;
	int sunset = 0;
	time_t midnight;
	struct tm tm;	

	time ( &rawtime );
	gmtime_r ( &rawtime, &ptm );

	tm.tm_year=ptm.tm_year;
	tm.tm_mon=ptm.tm_mon;
	tm.tm_mday=ptm.tm_mday;
	tm.tm_hour=0;
	tm.tm_min=0;
	tm.tm_sec=0;
	tm.tm_isdst = ptm.tm_isdst;

	midnight = mktime(&tm);

	hdate_get_utc_sun_time (ptm.tm_mday,ptm.tm_mon + 1,ptm.tm_year + 1900,latitude,longitude,&sunrise,&sunset);
	printf ("%.2f:%.2f %d:%d - %d:%d tz:%i\n", latitude,longitude,sunrise / 60, sunrise % 60, sunset / 60, sunset % 60,timezone);

	tSunrise = midnight + sunrise * 60 - timezone;
	tSunset = midnight + sunset * 60 - timezone;

	// next day
	rawtime += 86400;
	gmtime_r ( &rawtime, &ptm );
	hdate_get_utc_sun_time (ptm.tm_mday,ptm.tm_mon + 1,ptm.tm_year + 1900,latitude,longitude,&sunrise,&sunset);
	tSunriseTomorrow = midnight + 86400 + sunrise * 60 - timezone;
        tSunsetTomorrow = midnight + 86400 + sunset * 60 - timezone;

	return true;

}
