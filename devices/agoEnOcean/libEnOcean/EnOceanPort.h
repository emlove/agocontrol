/*
 Copyright 2008 Daniel Lechner, Andreas Dielacher
 see COPYING and COPYING.LESSER file for details.
 ============================================================================
 Name        : EnOceanPort
 Author      : Andreas Dielacher, Daniel Lechner
 Version     : 0.4.4
 Licence     : LGPL
 Description : Library for communication with EnOcean Evaluation Board (105)
 ============================================================================
*/

#ifndef ENOCEANPORT_H_
#define ENOCEANPORT_H_

#include "EnOceanProtocol.h"

/*! \mainpage EnOcean Port
This library is enables communication with the EnOcean Evaluation Board (105). It does all the work for you, like opening the serial port, sending data, receiving data and closing the connection in the end.
For the serial communication cssl is used (http://www.sourceforge.net/projects/cssl/).
This manual is divided in the following sections:
- \subpage intro
- \subpage advanced "Advanced usage"
- \subpage licence "Licence"
*/
//-----------------------------------------------------------
/*! \page intro Introduction
The library is written in C, so it should be useable on any platform where a C-compiler
is available. Nevertheless, up to now the library has only been tested under
Linux and MacOS.

To use this library, you only have to include the supplied header-files, you want to
use. For the basic usage, including EnOceanPort.h should be enough. If you want
to use the definitions and functions for the TCM120 module too, please include
TCM120.h too.
Inside this package you can also find the demo-program EnOceanPortTest.c, which should
give you some idea of how to use this library. If you want to have more insight, you
probably want to examine the code of the also available basic-GUI which is called
enoceanportbasicgui. If you have understood this pice of code, there should be no
open questions ;).

Now you can proceed to the \ref advanced "advanced section".
*/
//-----------------------------------------------------------
/*! \page advanced Advanced Usage
Well, the most important things have been mentioned in the \ref intro. Summarized:
Examine the code of the demo program and read the documentation of the available
functions. It should be no big deal to use this library.

But to make this section useful for you, I will give you the basic sequence of functions
which might be necessary to so something useful with the library:
First, call the \ref enocean_init function to open the port and examine the returned
\ref enocean_error_structure, if some error was returned. If everything went fine, proceed
with setting the callback-function which will be called if a frame was received. Use
the function \ref enocean_set_callback_function to do this. If you use the TCM120-module in the
EVA-board, feel free to construct some commands with the functions described in
\ref TCM120_functions and send the constructed \ref enocean_data_structure with the
\ref enocean_send command.

For a simple output of the received data frame, you can use the function
\ref enocean_printhex of \ref enocean_gethex in your callback-function.

After the job is done, you should call the \ref enocean_cleanup function to close the port
and free all unnecessary things.

Since this is everything the library is aware of, it is a good point for me to
stop here.
*/
//-----------------------------------------------------------
/*! \page licence Licence
This library makes use of the cssl library (http://www.sourceforge.net/projects/cssl).
The cssl is released under the LGPL.

EnOcean® and the EnOcean logo are registered trademarks of EnOcean
GmbH. All other product or service names are the property of their
respective owners. (EnOcean Brand Guidlines V2.0 August 2007)

This library is released under the GNU LGPL. For further details please have a look
into the files \ref COPYING and \ref COPYING.LESSER distributed with this library.
*/


/**
 * Data structure for errorhandling.
 */
typedef struct enocean_error_structure {
	int code; ///< errorcode
	const char* message; ///< additional message describing the error
} enocean_error_structure;

typedef void (*callback_func)(enocean_data_structure frame);

/// Program-error code, if everything was fine
#define E_OK 0
/// Program-error code, if the device cannot be opened
#define E_DEVICE_OPEN_FAILURE 1


/// Size of the read-ringbuffer
#define BUFSIZE 5

/**
 * @defgroup Definitions for the string representation
 * The definitions for the human-readable string representation
 * @{
 */
#define HR_TYPE "Type: "
#define HR_RPS  "RPS "
#define HR_1BS  "1BS "
#define HR_4BS  "4BS "
#define HR_HRC  "HRC "
#define HR_6DT  "6DT "
#define HR_MDA  "MDA "
#define HR_DATA " Data: "
#define HR_SENDER "Sender: "
#define HR_STATUS " Status: "
#define HR_CHECKSUM " Checksum: "
#define HR_TYPEUNKN "unknown "
/**
 * @}
 */

////////// communication functions //////////////
/**
 * This function initializes everything needed for the communication.
 * \param devicefile The devicefile for communication (e.g. /dev/ttyS0)
 * \return An error_structure which indicates an error
 */
enocean_error_structure enocean_init(const char* devicefile);

/**
 * Free all ports and other stuff which might have been reservated by the \ref enocean_init function.
 */
void enocean_cleanup();

/**
 * Function to send a defined number of bytes.
 * \param data The pointer to the place where the data is stored
 * \param size Number of bytes that should be transfered
 */
void enocean_send_raw(BYTE* data, int size);

/**
 * Function to send a whole datastructure. You don't have to think about messagesize, etc.
 * \param data Pointer to the data_structure, which will be sent
 */
void enocean_send(enocean_data_structure* data);

/**
 * Function to send a single byte (like the wake-telegram).
 * \param data Pointer to the single byte, which will be sent
 */
void enocean_send_byte(BYTE* data);

////////// datamanipulation functions //////////////
/**
 * \brief Calculate the correct checksum and return the value of it.
 *
 * Example usage: data.CHECKSUM = enocean_calc_checksum(data);
 *
 * \param input_data The package of which the checksum should be calculated
 * \return The value of the checksum
 */
BYTE enocean_calc_checksum(enocean_data_structure input_data);

/**
 * This function masks some bits from a byte and shifts them afterwards.
 *
 * Example:
 * data = 00110110
 * mask = 11110000
 * shift = 4
 * result = 0011
 *
 * \param data The byte-value which should be masked
 * \param mask The mask which should be applied
 * \param shifts The number of shifts
 */
int enocean_maskAndShift(BYTE data, BYTE mask, int shifts);

////////// construction of messages //////////////
/**
 * Construct a clean data structure filled with 0 (in the data fields)
 * \return A clean data structure
 */
enocean_data_structure enocean_clean_data_structure();

/**
 * Set the callback function which should be called, if a full frame was received
 * \param the_function The function which should be called, when a full frame was received
 */
void enocean_set_callback_function(callback_func the_function);

/**
 * Prints the contents of the frame in hexadecial
 * \param in The frame, which has to be converted
 */
void enocean_printhex(enocean_data_structure in);

/**
 * Like the function printhex, but returns the hexadecimal representation of the frame
 * as string. The caller has to free the returned char*!
 * \param in The frame, which has to be converted
 * \return The frame as string in hexview
 */
char* enocean_gethex(enocean_data_structure in);

/**
 * Like the function gethex, converts a single byte only.
 * \param in The byte, which has to be converted
 * \return The byte as string in hexview
 */
char* enocean_gethex_byte(BYTE in);

/**
 * This function returns a human-readable (and decoded) representation of the frame
 * as string. The caller has to free the returned char*!
 * \param frame The frame, which has to be converted
 * \return The frame as string in human-readable representation
 */
char* enocean_hexToHuman(enocean_data_structure frame);

#endif /*ENOCEANPORT_H_*/
