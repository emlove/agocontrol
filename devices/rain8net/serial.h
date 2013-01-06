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
#ifndef	_RS232_h_
#define	_RS232_h_

#ifndef	TIMEOUT_INFINITE
#define TIMEOUT_INFINITE	-1L
#endif	//	TIMEOUT_INFINITE

#ifndef	timeout_t
typedef long	timeout_t;
#endif

class Serial
{
public:

	enum Flow {
		flowNone,
		flowSoft,
		flowHard,
		flowBoth
	};
	typedef enum Flow Flow;

	enum Parity {
		parityNone,
		parityOdd,
		parityEven
	};
	typedef enum Parity Parity;

	enum Pending {
		pendingInput,
		pendingOutput,
		pendingError
	};
	typedef enum Pending Pending;

	virtual ~Serial();

	/**
	 * A serial object may be constructed from a named file on the
	 * file system.  This named device must be "isatty()".
	 *
	 * @param name of file.
	 */
	inline Serial()
	{}

	/**
	 * Used to properly initialize serial object.
	 *
 	 * @return 0 on success.  -1 if open fails. -2 if not a tty device.
	 * @param device name to open.
	 */
	int devInit(const char * f);

	/**
	 * Set serial port speed for both input and output.
	 * Default: 4800
	 *
 	 * @return 0 on success.
	 * @param speed to select. 0 signifies modem "hang up".
	 */
	int setSpeed(unsigned long speed);

	/**
	 * Get serial port speed
	 *
 	 * @return speed in bits per second
	 */
	unsigned long getSpeed(void);

	/**
	 * Set character size.
	 * Default: 8
	 *
	 * @return 0 on success.
	 * @param bits character size to use (usually 7 or 8).
	 */
	int setCharBits(int bits);

	/**
	 * Set parity mode.
	 * Default: None
	 *
	 * @return 0 on success.
	 * @param parity mode.
	 */
	int setParity(Parity parity);

	/**
	 * Set number of stop bits.
	 * Default: 1
	 *
	 * @return 0 on success.
	 * @param bits stop bits.
	 */
	int setStopBits(int bits);

	/**
	 * Set flow control.
	 *
	 * @return 0 on success.
	 * @param flow control mode.
	 */
	int setFlowControl(Flow flow);

	/**
	 * Get the number of bytes available to be read.
	 *
	 * @return 0 on success or errno.
	 * @param int item to receive byte count.  If return code is non-zero, this is undefined.
	 */
	int bytesAvailable(int & count);

	/**
	 * Raise the DTR signal.
	 *
	 */
	int raiseDTR(void);

	/**
	 * Lower the DTR signal.
	 *
	 */
	int lowerDTR(void);

	/**
	 * Set the DTR mode off momentarily.
	 *
	 * @param millisec number of milliseconds.
	 */
	int toggleDTR(timeout_t millisec);

	/**
	 * Send the "break" signal.
	 */
	void sendBreak(void);

	/**
	 * Get the status of pending operations.  This can be used to
	 * examine if input or output is waiting, or if an error has
	 * occured on the serial device.
	 *
	 * @return true if ready, false if timeout.
	 * @param pend ready check to perform.
	 * @param timeout in milliseconds.
	 */
	virtual bool isPending(Pending pend, timeout_t timeout = TIMEOUT_INFINITE);

	/**
	 * Reads from serial device.
	 *
	 * @param Data  Point to character buffer to receive data.  Buffers MUST
	 *				be at least Length + 1 bytes in size.
	 * @param Length Number of bytes to read.
	 */
	virtual int	devRead(char * Data, const int Length);

	/**
	 * Writes to serial device.
	 *
	 * @param Data  Point to character buffer containing data to write.  Buffers MUST
	 * @param Length Number of bytes to write.
	 */
	virtual int	devWrite(const char * Data, const int Length);

	/**
	 * Used to flush the input waiting queue.
	 */
	void flushInput(void);

	/**
	 * Used to flush any pending output data.
	 */
	void flushOutput(void);

	void wait(timeout_t ms);

protected:

	int	comDevice;

	/**
	 * Opens the serial device.
	 *
	 * @param fname Pathname of device to open
	 */
	int	devOpen(const char *fname);

	/**
	 * Closes the serial device.
	 *
	 */
	void devClose(void);

	/**
	 * Restore serial device to the original settings at time of open.
	 */
	void restore(void);

	/**
	 * Used to wait until all output has been sent.
	 */
	void waitOutput(void);

	/**
	 * Used as the default destructor for ending serial I/O
	 * services.  It will restore the port to it's original state.
	 */
	void endSerial(void);

	/**
	 * Used to initialize a newly opened serial file handle.  You
	 * should set serial properties and DTR manually before first
	 * use.
	 */
	void initConfig(void);


private:
	
	void	*	original;
	void	*	current;
};


#endif	//	_RS232_h_

