/*
 * Written by and Copyright (C) 2008 the SourceForge
 * 	Rain8Net team. http://rain8net.sourceforge.net/
 *
 * This file is part of Rain8Net.
 * 
 * Rain8Net is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Rain8Net is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with Rain8Net.  If not, see <http://www.gnu.org/licenses/>.
 *
 */
#include <exception>
#include <memory>

#include "serial.h"

class ZoneRangeException : public std::exception
{
public:

	inline ZoneRangeException()
	{}

	virtual const char *what() const throw()
	{
		return "Zone number is out of range (1-8)";
	}
	inline virtual ~ZoneRangeException() throw()
	{}
};

class UnitRangeException : public std::exception
{
public:

	inline UnitRangeException()
	{}

	virtual const char *what() const throw()
	{
		return "Unit number is out of range (1-254)";
	}
	inline virtual ~UnitRangeException() throw()
	{}
};

#define RAIN8_MAX_ZONE_COUNT		8
#define RAIN8_MAX_UNIT_COUNT		254
#define RAIN8_VALIDATE_ZONE(a)	{ if (0 >= (a) || RAIN8_MAX_ZONE_COUNT < (a)) throw ZoneRangeException(); }
#define RAIN8_VALIDATE_UNIT(a)	{ if (0 >= (a) || RAIN8_MAX_UNIT_COUNT < (a)) throw UnitRangeException(); }

#define RAIN8_COMMAND_LENGTH		3
#define	RAIN8_CLEAR_COMMAND(a)	{ memset((a), 0, RAIN8_COMMAND_LENGTH); }
#define RAIN8_INIT_COMMAND_LENGTH	32
#define	RAIN8_CLEAR_INIT_COMMAND(a)	{ memset((a), 0, RAIN8_INIT_COMMAND_LENGTH); }

#define RAIN8_COMMAND_TIMEOUT		(-1)
#define	RAIN8_COMMAND_FAILURE		(-2)
#define	RAIN8_COMMAND_SUCCESS		(0)


class rain8zone
{
public:
	inline rain8zone() : TheDefaultTime(60)
	{}

	inline void setTime(const unsigned char t)
	{
		TheDefaultTime = t;
	}

	inline const unsigned char getTime(void)
	{
		return TheDefaultTime;
	}

	inline void setOn(bool s)
	{
		OnStatus = s;
	}

	inline bool isOn(void)
	{
		return OnStatus;
	}

	inline virtual ~rain8zone()
	{}

private:

	unsigned char	TheDefaultTime;
	bool			OnStatus;
};


class rain8unit
{
public:

	inline rain8unit(const unsigned char a)
		:	TheAddress(a)
	{}

	int initUnit(void);

	inline void setAddress(const unsigned char u)
	{
		TheAddress = u;
	}
	inline const unsigned char getAddress(void)
	{
		return TheAddress;
	}

	inline void zoneOn(const unsigned char zone)
	{
		RAIN8_VALIDATE_ZONE(zone);
	}

	inline void zoneOff(const unsigned char zone)
	{
		RAIN8_VALIDATE_ZONE(zone);
	}

	inline bool isZoneOn(const unsigned char zone)
	{
		RAIN8_VALIDATE_ZONE(zone);
		return TheZones[zone].isOn();
	}


	inline virtual ~rain8unit()
	{}


private:

	unsigned char	TheAddress;
	rain8zone		TheZones[RAIN8_MAX_ZONE_COUNT];

};

class rain8net : public Serial
{
public:

	inline rain8net() : TimeoutValue(5000L)
	{}

	int init(const char * device = "/dev/ttyS0");

	/**
	 * Set the timer values for the selected unit.
	 *
	 * @param unit number for command
	 * @param defaulttimes array of timer values
	 * @returns 0 if successful, -1 if no response, -2 if command failed, or errno
	 */
	int setZoneTimers(const unsigned char unit, const unsigned char defaulttimes[]);

	/**
	 * Get the timer values for the selected unit.
	 *
	 * @param unit number for command
	 * @param defaulttimes array of timer values
	 * @returns 0 if successful, -1 if no response, -2 if command failed, or errno
	 */
	int getZoneTimers(const unsigned char unit, unsigned char defaulttimes[]);


	/**
	 *	Set the timeout for read operations to the device
	 *
	 *	@param timeout in milliseconds
	 */
	void setTimeout(const long t = 1000L)
	{
		TimeoutValue = t;
	}

	/**
	 *	Get the timeout for read operations to the device
	 *
	 *	@return timeout in milliseconds
	 */
	const long getTimeout(void)
	{
		return TimeoutValue;
	}

	/**
	 *	Turn off all zones
	 *
	 *	@param unit number for command
	 *	@returns 0 if successful, -1 if no response or errno
	 */
	int allOff(const unsigned char unit);

	/**
	 *	Get the zone status byte
	 *
	 *	@param unit number for command
	 *	@param zone status byte.  Each bit corresponds to the ON/OFF status of the
	 *		relative zone.  A status of 0x34 (binary 00110100) corresponds to zones 
	 *		3, 5 and 6 being ON. 
	 *	@returns 0 if successful, -1 if no response or errno
	 */
	int getStatus(const unsigned char unit, unsigned char & status);

	/**
	 *	Turn on a zone
	 *
	 *	@param unit number for command
	 *	@param zone number to turn on
	 *	@returns 0 if successful, -1 if no response or errno
	 */
	int zoneOn(const unsigned char unit, const unsigned char zone);

	/**
	 *	Turn off a zone
	 *
	 *	@param unit number for command
	 *	@param zone number to turn off
	 *	@returns 0 if successful, -1 if no response or errno
	 */
	int zoneOff(const unsigned char unit, const unsigned char zone);

	/**
	 *	Sends a COM Check packet (70h + 2 bytes) to the device
	 *
	 *	@returns 0 if successful, -1 if no response or errno
	 */
	int comCheck(void);


	/**
	 * Turns off all zones in all units.
	 *
	 * @returns 0 if successfull, errno in the case of failure
	 */
	int globalAllOff(void);

protected:

	int		TheDevice;		//	The device handle
	long	TimeoutValue;

private:

	//	Hide and Disallow
	//
	rain8net(const rain8net &);
	rain8net & operator=(const rain8net &);

};

