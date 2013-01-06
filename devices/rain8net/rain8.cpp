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
#include <unistd.h>
#include <cstdlib>
#include <cerrno>
#include <string.h>
#include "rain8.h"

int rain8net::init(const char * device)
{
	int rc = devInit(device);

	if (0 != rc)
		return rc;
	rc = setSpeed(4800);
	if (0 != rc)
		return rc;
	rc = setCharBits(8);
	if (0 != rc)
		return rc;
	rc = setStopBits(1);
	if (0 != rc)
		return rc;
	rc = setParity(Serial::parityNone);
	if (0 != rc)
		return rc;
	rc = setFlowControl(Serial::flowNone);
	if (0 != rc)
		return rc;

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::setZoneTimers(const unsigned char unit, const unsigned char defaulttimes[])
{
	int i = 0;
	char command[RAIN8_COMMAND_LENGTH];
	char cTempResponse = 0;
	char response[RAIN8_INIT_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_INIT_COMMAND(response);
	RAIN8_VALIDATE_UNIT(unit);

	command[0] = 0x21;
	command[1] = 0x21;
	command[2] = 0x21;

	int cnt = devWrite(command, RAIN8_COMMAND_LENGTH);

	if (RAIN8_COMMAND_LENGTH != cnt)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	cnt = devRead(&cTempResponse, 1);
	if (-1 == cnt)
		return errno;

	if ((1 != cnt) || (0x22 != cTempResponse))
		return RAIN8_COMMAND_FAILURE;

	response[0] = unit;
	response[6] = 0x01; /* Enable timers. */
	response[7] = 0x55;
	for (i = 0; i < 8; i++)
	{
		response[i + 24] = static_cast<unsigned char>(defaulttimes[i]);
	}

	cnt = devWrite(response, RAIN8_INIT_COMMAND_LENGTH);
	if (-1 == cnt)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	cnt = devRead(&cTempResponse, 1);
	if (-1 == cnt)
		return errno;

	if ((1 != cnt) || (0x63 != cTempResponse))
		return RAIN8_COMMAND_FAILURE;

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::getZoneTimers(const unsigned char unit, unsigned char defaulttimes[])
{
	int i = 0;
	char command[RAIN8_COMMAND_LENGTH];
	char response[RAIN8_INIT_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_INIT_COMMAND(response);
	RAIN8_VALIDATE_UNIT(unit);

	for (i = 0; i < 8; i++)
	{
		defaulttimes[i] = 0;
	}

	command[0] = 0x23;
	command[1] = 0x23;
	command[2] = 0x23;

	int cnt = devWrite(command, RAIN8_COMMAND_LENGTH);

	if (RAIN8_COMMAND_LENGTH != cnt)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	int iTotalCnt = 0;
	do
	{
		cnt = devRead(response + iTotalCnt, RAIN8_INIT_COMMAND_LENGTH - iTotalCnt);
		if (-1 == cnt)
			return errno;

		iTotalCnt += cnt;

		if (RAIN8_INIT_COMMAND_LENGTH != iTotalCnt)
		{
			if (!isPending(Serial::pendingInput, TimeoutValue))
			{
				return RAIN8_COMMAND_TIMEOUT;
			}
		}
	} while (RAIN8_INIT_COMMAND_LENGTH != iTotalCnt);

	if (RAIN8_INIT_COMMAND_LENGTH != iTotalCnt)
		return RAIN8_COMMAND_FAILURE;

	for (i = 0; i < 8; i++)
	{
		defaulttimes[i] = response[i + 24];
	}

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::allOff(const unsigned char unit)
{
	char command[RAIN8_COMMAND_LENGTH];
	char response[RAIN8_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_COMMAND(response);
	RAIN8_VALIDATE_UNIT(unit);

	command[0] = 0x40;
	command[1] = unit;
	command[2] = 0x55;

	int cnt = devWrite(command, 3);

	if (RAIN8_COMMAND_LENGTH != cnt)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	cnt = devRead(response, RAIN8_COMMAND_LENGTH);
	if (-1 == cnt)
		return errno;

	if ((RAIN8_COMMAND_LENGTH != cnt) || (0 != memcmp(command, response, 3)))
		return RAIN8_COMMAND_FAILURE;

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::getStatus(const unsigned char unit, unsigned char & status)
{
	char command[RAIN8_COMMAND_LENGTH];
	char response[RAIN8_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_COMMAND(response);
	RAIN8_VALIDATE_UNIT(unit);

	command[0] = 0x40;
	command[1] = unit;
	command[2] = 0xF0;

	int rc = devWrite(command, 3);

	if (RAIN8_COMMAND_LENGTH != rc)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	int cnt = devRead(response, RAIN8_COMMAND_LENGTH);
	if (-1 == cnt)
		return errno;

	if (RAIN8_COMMAND_LENGTH != cnt)
		return RAIN8_COMMAND_FAILURE;

	status = response[2];

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::zoneOn(const unsigned char unit, const unsigned char zone)
{
	char command[RAIN8_COMMAND_LENGTH];
	char response[RAIN8_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_COMMAND(response);
	RAIN8_VALIDATE_UNIT(unit);
	RAIN8_VALIDATE_ZONE(zone);

	command[0] = 0x40;
	command[1] = unit;
	command[2] = (0x30 | zone);

	int rc = devWrite(command, 3);

	if (RAIN8_COMMAND_LENGTH != rc)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	int cnt = devRead(response, RAIN8_COMMAND_LENGTH);
	if (-1 == cnt)
		return errno;

	if ((RAIN8_COMMAND_LENGTH != cnt) || (0 != memcmp(command, response, 3)))
		return RAIN8_COMMAND_FAILURE;


	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::zoneOff(const unsigned char unit, const unsigned char zone)
{
	char command[RAIN8_COMMAND_LENGTH];
	char response[RAIN8_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_COMMAND(response);
	RAIN8_VALIDATE_UNIT(unit);
	RAIN8_VALIDATE_ZONE(zone);

	command[0] = 0x40;
	command[1] = unit;
	command[2] = (0x40 | zone);

	int rc = devWrite(command, 3);

	if (RAIN8_COMMAND_LENGTH != rc)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	int cnt = devRead(response, RAIN8_COMMAND_LENGTH);
	if (-1 == cnt)
		return errno;

	if ((RAIN8_COMMAND_LENGTH != cnt) || (0 != memcmp(command, response, 3)))
		return RAIN8_COMMAND_FAILURE;

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::comCheck(void)
{
	char command[RAIN8_COMMAND_LENGTH];
	char response[RAIN8_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);
	RAIN8_CLEAR_COMMAND(response);

	command[0] = 0x70;
	command[1] = 0x70;
	command[2] = 0x70;

	int rc = devWrite(command, 3);

	if (RAIN8_COMMAND_LENGTH != rc)
		return errno;

	if (!isPending(Serial::pendingInput, TimeoutValue))
		return RAIN8_COMMAND_TIMEOUT;

	int cnt = devRead(response, RAIN8_COMMAND_LENGTH);
	if (-1 == cnt)
		return errno;

	if (RAIN8_COMMAND_LENGTH != cnt)
		return RAIN8_COMMAND_FAILURE;

	return RAIN8_COMMAND_SUCCESS;
}

int rain8net::globalAllOff(void)
{
	char command[RAIN8_COMMAND_LENGTH];

	RAIN8_CLEAR_COMMAND(command);

	command[0] = 0x20;
	command[1] = 0x55;
	command[2] = 0x55;

	int cnt = devWrite(command, 3);

	if (RAIN8_COMMAND_LENGTH != cnt)
		return errno;

//	if (!isPending(Serial::pendingInput, TimeoutValue))
////		return RAIN8_COMMAND_TIMEOUT;

	return RAIN8_COMMAND_SUCCESS;
}

