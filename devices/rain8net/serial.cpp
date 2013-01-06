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
#include <cstdlib>
#include <climits>
#include <termios.h>
#include <cerrno>
#include <memory.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <poll.h>
#include <time.h>
#include <unistd.h>

#include "serial.h"

#ifndef	MAX_INPUT
#define	MAX_INPUT 255
#endif

#ifndef MAX_CANON
#define MAX_CANON MAX_INPUT
#endif


#ifndef	CRTSCTS
#ifdef	CNEW_RTSCTS
#define	CRTSCTS (CNEW_RTSCTS)
#endif
#endif

#if defined(CTSXON) && defined(RTSXOFF) && !defined(CRTSCTS)
#define	CRTSCTS (CTSXON | RTSXOFF)
#endif

#ifndef	CRTSCTS
#define	CRTSCTS	0
#endif

int Serial::devInit(const char *fname)
{
	comDevice = -1;
	current = new struct termios;
	original = new struct termios;

	devOpen(fname);

	if (-1 == comDevice)
		return -1;

	if(!isatty(comDevice)) 
	{
		devClose();
		return -2;
	}
	return 0;
}

Serial::~Serial()
{
	endSerial();
}

void Serial::initConfig(void)
{

	fcntl(comDevice, F_SETFL, FNDELAY);
	
	tcgetattr(comDevice, (struct termios *)original);

	bzero(current, sizeof(struct termios));
	
	((struct termios *)current)->c_cc[VMIN] = 0;
	((struct termios *)current)->c_cc[VTIME] = 0;
	
	((struct termios *)current)->c_oflag &= ~OPOST;
	((struct termios *)current)->c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
	((struct termios *)current)->c_cflag &= ~(PARENB | CSTOPB | CSIZE);
	((struct termios *)current)->c_cflag |= (CRTSCTS|CREAD|CLOCAL|CS8);
	((struct termios *)current)->c_iflag |= (INPCK | ISTRIP);
	
	cfsetispeed(((struct termios *)current), B4800);
	cfsetospeed(((struct termios *)current), B4800);
	
	tcsetattr(comDevice, TCSANOW, (struct termios *)current);
	
}

void Serial::restore(void)
{
	memcpy(current, original, sizeof(struct termios));
	tcsetattr(comDevice, TCSANOW, (struct termios *)current);
}

void Serial::endSerial(void)
{
	if(comDevice < 0 && original)
		tcsetattr(comDevice, TCSANOW, (struct termios *)original);

	if(current)
		delete (struct termios *)current;

	if(original)
		delete (struct termios *)original;

	devClose();

	current = NULL;
	original = NULL;

}

void Serial::flushInput(void)
{
	tcflush(comDevice, TCIFLUSH);
}

void Serial::flushOutput(void)
{
	tcflush(comDevice, TCOFLUSH);
}

void Serial::waitOutput(void)
{
	tcdrain(comDevice);
}

int Serial::devOpen(const char * fname)
{
	int cflags = O_RDWR | O_NDELAY | O_NOCTTY;
	comDevice = open(fname, cflags);
	if (-1 == comDevice)
		return -1;

	initConfig();
	return 0;
}

int Serial::devRead(char *Data, const int Length)
{
	return read(comDevice, Data, Length);
}

int Serial::devWrite(const char *Data, const int Length)
{
	return write(comDevice, Data, Length);
}

void Serial::devClose()
{
	close(comDevice);
	comDevice = -1;
}


int Serial::setSpeed(unsigned long speed)
{
	unsigned long rate = B4800;

	switch(speed) 
	{
#ifdef B115200
		case 115200:
			rate = B115200;
			break;
#endif
#ifdef B57600
		case 57600:
			rate = B57600;
			break;
#endif
#ifdef B38400
		case 38400:
			rate = B38400;
			break;
#endif
		case 19200:
			rate = B19200;
			break;
		case 9600:
			rate = B9600;
			break;
		case 4800:
			rate = B4800;
			break;
		case 2400:
			rate = B2400;
			break;
		case 1200:
			rate = B1200;
			break;
		case 600:
			rate = B600;
			break;
		case 300:
			rate = B300;
			break;
		case 110:
			rate = B110;
			break;
#ifdef	B0
		case 0:
			rate = B0;
			break;
#endif
	}

	struct termios *attr = (struct termios *)current;
	cfsetispeed(attr, rate);
	cfsetospeed(attr, rate);
	if (0 != tcsetattr(comDevice, TCSANOW, attr))
		return errno;

	return 0;
}

unsigned long Serial::getSpeed(void)
{
	unsigned long speed = 0;
	unsigned long rate = B2400;
	struct termios *attr = (struct termios *)current;
	tcgetattr(comDevice, attr);
	rate = cfgetispeed(attr);
	
	switch(rate) 
	{
#ifdef B115200
		case B115200:
			speed = 115200;
			break;
#endif
#ifdef B57600
		case B57600:
			speed = 57600;
			break;
#endif
#ifdef B38400
		case B38400:
			speed = 38400;
			break;
#endif
		case B19200:
			speed = 19200;
			break;
		case B9600:
			speed = 9600;
			break;
		case B4800:
			speed = 4800;
			break;
		case B2400:
			speed = 2400;
			break;
		case B1200:
			speed = 1200;
			break;
		case B600:
			speed = 600;
			break;
		case B300:
			speed = 300;
			break;
		case B110:
			speed = 110;
			break;
#ifdef	B0
		case B0:
			speed = 0;
			break;
#endif
	}

	return speed;
}

int Serial::setFlowControl(Flow flow)
{

	struct termios *attr = (struct termios *)current;

	attr->c_cflag &= ~CRTSCTS;
	attr->c_iflag &= ~(IXON | IXANY | IXOFF);

	switch(flow) {
	case flowSoft:
		attr->c_iflag |= (IXON | IXANY | IXOFF);
		break;
	case flowBoth:
		attr->c_iflag |= (IXON | IXANY | IXOFF);
	case flowHard:
		attr->c_cflag |= CRTSCTS;
		break;
	case flowNone:
	default:
		break;
	}

	if (0 != tcsetattr(comDevice, TCSANOW, attr))
		return errno;

	return 0;
}

int Serial::setStopBits(int bits)
{
	struct termios *attr = (struct termios *)current;
	attr->c_cflag &= ~CSTOPB;

	switch(bits) 
	{
	case 2:
		attr->c_cflag |= CSTOPB;
		break;
	}

	if (0 != tcsetattr(comDevice, TCSANOW, attr))
		return errno;

	return 0;
}

int Serial::setCharBits(int bits)
{
	struct termios *attr = (struct termios *)current;
	attr->c_cflag &= ~CSIZE;

	switch(bits) 
	{
	case 5:
		attr->c_cflag |= CS5;
		break;
	case 6:
		attr->c_cflag |= CS6;
		break;
	case 7:
		attr->c_cflag |= CS7;
		break;
	case 8:
	default:
		attr->c_cflag |= CS8;
		break;
	}

	if (0 != tcsetattr(comDevice, TCSANOW, attr))
		return errno;

	return 0;
}

int Serial::setParity(Parity parity)
{
	struct termios *attr = (struct termios *)current;
	attr->c_cflag &= ~(PARENB | PARODD);

	switch(parity) 
	{
	case parityEven:
		attr->c_cflag |= PARENB;
		break;
	case parityOdd:
		attr->c_cflag |= (PARENB | PARODD);
		break;
	case parityNone:
	default:
		break;
	}

	if (0 != tcsetattr(comDevice, TCSANOW, attr))
		return errno;

	return 0;
}

void Serial::sendBreak(void)
{
	tcsendbreak(comDevice, 0);
}

int Serial::bytesAvailable(int & count)
{
	int bytes = 0;
	int rc = ioctl(comDevice, FIONREAD, &bytes);
	if (-1 == rc)
	{
		count = 0;
		return errno;
	}
	count = bytes;
	return 0;
}

int Serial::raiseDTR(void)
{
	int status;

	int rc = ioctl(comDevice, TIOCMGET, &status);
	if (-1 == rc)
		return errno;

	status &= ~TIOCM_DTR;

	rc = ioctl(comDevice, TIOCMGET, &status);
	if (-1 == rc)
		return errno;

	return 0;
}

int Serial::lowerDTR(void)
{
	int status;

	int rc = ioctl(comDevice, TIOCMGET, &status);
	if (-1 == rc)
		return errno;

	status |= TIOCM_DTR;

	rc = ioctl(comDevice, TIOCMGET, &status);
	if (-1 == rc)
		return errno;

	return 0;
}

int Serial::toggleDTR(timeout_t millisec)
{
	int rc = lowerDTR();
	if (rc)
		return rc;

	if(millisec) 
	{
		wait(millisec);
		rc = lowerDTR();
		if (rc)
			return rc;
	}
	return 0;
}

void Serial::wait(timeout_t ms)
{
	struct timespec t;
	t.tv_sec = ms / 1000;
	t.tv_nsec = ((ms % 1000) * 1000000l);
	nanosleep(&t, 0);
}

bool Serial::isPending(Pending pending, timeout_t timeout)
{

	int status;
	struct pollfd pfd;

	pfd.fd = comDevice;
	pfd.revents = 0;
	switch(pending) 
	{
	case pendingInput:
		pfd.events = POLLIN;
		break;
	case pendingOutput:
		pfd.events = POLLOUT;
		break;
	case pendingError:
		pfd.events = POLLERR | POLLHUP;
		break;
	}

	status = 0;
	while(status < 1) 
	{
		if(timeout == TIMEOUT_INFINITE)
			status = poll(&pfd, 1, -1);
		else
			status = poll(&pfd, 1, timeout);

		if(status < 1) 
		{
			if(status == -1 && errno == EINTR)
				continue;
			return false;
		}
	}

	if(pfd.revents & pfd.events)
		return true;

	return false;
}

