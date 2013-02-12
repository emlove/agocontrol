/*
 * Copyright 2008 (c) Scott Reid, dataczar.net
 * $Id$
*/

#include <limits.h>
#include <list>
#include <vector>
#include <arduino.h>

#define FIRMATA_MAX_DATA_BYTES            32 // max number of data bytes in non-Sysex messages
#define FIRMATA_DEFAULT_BAUD          57600
#define FIRMATA_FIRMWARE_VERSION_SIZE      2 // number of bytes in firmware version

// message command bytes (128-255/0x80-0xFF)
#define FIRMATA_DIGITAL_MESSAGE         0x90 // send data for a digital pin
#define FIRMATA_ANALOG_MESSAGE          0xE0 // send data for an analog pin (or PWM)
#define FIRMATA_ANALOG_MESSAGE          0xE0 // send data for an analog pin (or PWM)
#define FIRMATA_REPORT_ANALOG           0xC0 // enable analog input by pin #
#define FIRMATA_REPORT_DIGITAL          0xD0 // enable digital input by port pair
//
#define FIRMATA_SET_PIN_MODE            0xF4 // set a pin to INPUT/OUTPUT/PWM/etc
//
#define FIRMATA_REPORT_VERSION          0xF9 // report protocol version
#define FIRMATA_SYSTEM_RESET            0xFF // reset from MIDI
//
#define FIRMATA_START_SYSEX             0xF0 // start a MIDI Sysex message
#define FIRMATA_END_SYSEX               0xF7 // end a MIDI Sysex message

// extended command set using sysex (0-127/0x00-0x7F)
/* 0x00-0x0F reserved for custom commands */
#define FIRMATA_SERVO_CONFIG            0x70 // set max angle, minPulse, maxPulse, freq
#define FIRMATA_STRING                  0x71 // a string message with 14-bits per char
#define FIRMATA_REPORT_FIRMWARE         0x79 // report name and version of the firmware
#define FIRMATA_SYSEX_NON_REALTIME      0x7E // MIDI Reserved for non-realtime messages
#define FIRMATA_SYSEX_REALTIME          0x7F // MIDI Reserved for realtime messages

// pin modes
#define FIRMATA_INPUT                   0x00 // digital pin in digitalInput mode
#define FIRMATA_OUTPUT                  0x01 // digital pin in digitalOutput mode
#define FIRMATA_ANALOG                  0x02 // analog pin in analogInput mode
#define FIRMATA_PWM                     0x03 // digital pin in PWM output mode
#define FIRMATA_SERVO                   0x04 // digital pin in Servo output mode

using namespace std;

class Firmata {
	public:
		Firmata();
		Firmata(const char* _serialPort);
		~Firmata();

		int destroy();
		int openPort(const char* _serialPort);
		int openPort(const char* _serialPort, const int _baud);
		int writeDigitalPin(unsigned char pin, unsigned char mode); // mode can be ARDUINO_HIGH or ARDUINO_LOW
		int setPinMode(unsigned char pin, unsigned char mode);
		int setPwmPin(unsigned char pin, int16_t value);
		char* getFirmwareVersion();
		int systemReset();
		int closePort();
		int flushPort();
		int getSysExData();
		int sendSysExData(const unsigned char command, vector<unsigned char> data);

	protected:

		Arduino* arduino;
		bool portOpen;
		int waitForData;
		int executeMultiByteCommand;
		int multiByteChannel;
		unsigned char serialInBuf[FIRMATA_MAX_DATA_BYTES];
		unsigned char serialOutBuf[FIRMATA_MAX_DATA_BYTES];

		vector<unsigned char> sysExBuf;
		char firmwareVersion[FIRMATA_FIRMWARE_VERSION_SIZE];
		int digitalPortValue[ARDUINO_DIG_PORTS]; /// bitpacked digital pin state
		int init();
    int sendValueAsTwo7bitBytes(int value);
};
