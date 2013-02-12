/*
 * Copyright (c) 2008 - Scott Reid, dataczar.com
 * $Id$
 * 
 * Based on:
 * cppglue http://code.google.com/p/cppglue/
 * Copyright 2007 (c) Erik Sjodin, eriksjodin.net
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use,
 * copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following
 * conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial _portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 * OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 */

#include <firmata.h>

Firmata::Firmata() {
	init();
}

Firmata::Firmata(const char* _serialPort) {
	init();
	if (openPort(_serialPort) == 0) {
		portOpen = 1;
	}
}

Firmata::~Firmata() {
	destroy();
}

int Firmata::destroy() {
	int rv = 0;
	delete arduino;
	return rv;
}

int Firmata::openPort(const char* _serialPort) {
	return(arduino->openPort(_serialPort,FIRMATA_DEFAULT_BAUD));
}

int Firmata::openPort(const char* _serialPort, const int _baud) {
	if(arduino->openPort(_serialPort,_baud) < 0) {
		perror("Firmata::openPort:arduino->openPort()");
		closePort();
		return(-1);
	}
	return(0);
}

int Firmata::writeDigitalPin(unsigned char pin, unsigned char mode) {
	int rv = 0;
  int bit;
  int port;
  if(pin < 8 && pin >1){
    port=0;
    bit = pin;
  }
  else if(pin>7 && pin <14){
    port = 1;
    bit = pin-8;
  }
  else if(pin>15 && pin <22){
    port = 2;
    bit = pin-16;
  }
  else {
    return(-2);
  }
	// set the bit
	if(mode==ARDUINO_HIGH)
		digitalPortValue[port] |= (1 << bit);

	// clear the bit        
	else if(mode==ARDUINO_LOW)
		digitalPortValue[port] &= ~(1 << bit);
	
	else {
		perror("Firmata::writeDigitalPin():invalid mode:");
		return(-1);
	}
	rv |= arduino->sendUchar(FIRMATA_DIGITAL_MESSAGE+port);
	rv |= sendValueAsTwo7bitBytes(digitalPortValue[port]); //ARDUINO_HIGH OR ARDUINO_LOW
	return(rv);
}

// in Firmata (and MIDI) data bytes are 7-bits. The 8th bit serves as a flag to mark a byte as either command or data.
// therefore you need two data bytes to send 8-bits (a char).  
int Firmata::sendValueAsTwo7bitBytes(int value)
{
  int rv = 0;
  rv |= arduino->sendUchar(value & 127); // LSB
  rv |= arduino->sendUchar(value >> 7 & 127); // MSB
  return rv;
}

int Firmata::setPinMode(unsigned char pin, unsigned char mode) {
	int rv = 0;
	rv |= arduino->sendUchar(FIRMATA_SET_PIN_MODE);
	rv |= arduino->sendUchar(pin);
	rv |= arduino->sendUchar(mode);
  return(rv);
}

int Firmata::setPwmPin(unsigned char pin, int16_t value) {
	int rv=0;
	rv |= arduino->sendUchar(FIRMATA_ANALOG_MESSAGE+pin);
	rv |= arduino->sendUchar((unsigned char)(value % 128));
	rv |= arduino->sendUchar((unsigned char)(value >> 7));
	return(rv);
}

char* Firmata::getFirmwareVersion() {
	char* tmp = firmwareVersion;
	return tmp;
}

int Firmata::systemReset() {
	int rv=0;
	rv |= arduino->sendUchar(FIRMATA_SYSTEM_RESET);
	return(rv);
}

int Firmata::closePort() {
	if(arduino->closePort() < 0) {
		perror("Firmata::closePort():arduino->closePort():");
		portOpen = 0;
		return(-1);
	}
	return(0);
}

int Firmata::flushPort() {
	if(arduino->flushPort() < 0) {
		perror("Firmata::flushPort():arduino->flushPort():");
		return(-1);
	}
	return(0);
}

int Firmata::sendSysExData(const unsigned char command, vector<unsigned char> data) {
	int rv=0;
	rv |= arduino->sendUchar(FIRMATA_START_SYSEX);
	rv |= arduino->sendUchar(command);
	vector<unsigned char>::iterator it = data.begin();
	while (it != data.end()) {
		rv |= arduino->sendUchar(*it);
		it++;
	}
	rv |= arduino->sendUchar(FIRMATA_END_SYSEX);
	return(rv);
}

int Firmata::init() {
	waitForData = 0;
	for (int i=0; i<ARDUINO_DIG_PORTS; i++) {
    digitalPortValue[3] = 0;
  }
	portOpen = 0;
	arduino = new Arduino();
	return 0;
}
