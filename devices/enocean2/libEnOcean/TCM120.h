/*
 Copyright 2008 Daniel Lechner, Andreas Dielacher
 see COPYING and COPYING.LESSER file for details.
*/

#ifndef TCM120_H_
#define TCM120_H_

#include "EnOceanProtocol.h"

/**
 * @defgroup org120 Type of telegram (TCT for TCM 120)
 * Type definition of the telegram - Command Telegrams and Messages for TCM 120
 * @{
*/
/**
 * \brief Init response
 *
 * After a power-on, a hardware reset or a RESET command the
 * TCM informs the user through several of these telegrams about
 * the current status.
 * The messages have the general syntax as shown on the left.
 * The information contained by the bytes marked as X should be
 * decoded according to ASCII code.
 */
#define C_ORG_INF_INIT 0x89
/**
 * \brief Positive response
 *
 * Standard message used to confirm that an action was
 * performed correctly by the TCM.
 */
#define C_ORG_OK 0x58
/**
 * \brief Error response
 *
 * Standard error message response if after a TCT command the
 * operation could not be carried out successfully by the TCM.
 */
#define C_ORG_ERR 0x19
/**
 * \brief Rewrite ID range base
 *
 * With this command the user can rewrite its ID range base number.
 */
#define C_ORG_SET_IDBASE 0x18
/**
 * \brief Receive ID range base
 *
 * When this command is sent to the TCM, the base ID range
 * number is retrieved though an INF_IDBASE telegram.
 */
#define C_ORG_RD_IDBASE 0x58
/**
 * \brief Actual ID range base
 *
 * This message informs the user about the ID range base number.
 * IDBaseByte3 is the most significant byte.
 */
#define C_ORG_INF_IDBASE 0x98
/**
 * \brief Set the receive sensitivity
 *
 * This command is used to set the TCM radio sensitivity.
 * In LOW radio sensitivity, signals from remote transmitters are
 * not detected by the TCM receiver. This feature is useful when
 * only information from transmitters in the vicinity should be
 * processed. An OK confirmation telegram is generated after TCM
 * sensitivity has been changed.
 */
#define C_ORG_SET_RX_SENSITIVITY 0x08
/**
 * \brief Receive the receive sensitivity
 *
 * This command is sent to the TCM to retrieve the current radio
 * sensitivity mode (HIGH or LOW).
 * This information is sent via a INF_RX_SENSITIVITY command.
 */
#define C_ORG_RD_RX_SENSITIVITY 0x48
/**
 * \brief Actual receive sensitivity
 *
 * This message informs the user about the current TCM radio sensitivity.
 */
#define C_ORG_INF_RX_SENSITIVITY 0x88
/**
 * \brief Set sleep mode
 *
 * If the TCM receives the SLEEP command, it works in an energysaving mode.
 * The TCM will not wake up before a hardware reset
 * is made or a WAKE telegram is sent via the serial interface.
 */
#define C_ORG_SLEEP 0x09
#define C_TELEGRAM_WAKE 0xAA
/**
 * \brief Reset the TCM 120 module
 *
 * Performs a reset of the TCM microcontroller. When the TCM is
 * ready to operate again, it sends an ASCII message (INF_INIT)
 * containing the current settings.
 */
#define C_ORG_RESET 0x0A
/**
 * \brief Turn on Modem mode
 *
 * Activates TCM modem functionality and sets the modem ID. An
 * OK confirmation telegram is generated. The modem ID is the ID
 * at which the TCM receives messages of type 6DT.
 * The modem ID and modem status (ON/OFF) is stored in
 * EEPROM. The modem ID range is from 0x0001 to 0xFFFF.
 * IF 0x0000 is provided as modem ID, the modem is activated
 * with the ID previously stored in EEPROM.
 */
#define C_ORG_MODEM_ON 0x28
#define C_ORG_MODEM_OFF 0x2A
#define C_ORG_RD_MODEM_STATUS 0x68
#define C_ORG_INF_MODEM_STATUS 0xA8
#define C_ORG_RD_SW_VER 0x4B
#define C_ORG_INF_SW_VER 0x8C
#define C_ORG_ERR_MODEM_NOTWANTEDACK 0x28
#define C_ORG_ERR_MODEM_NOTACK 0x29
#define C_ORG_ERR_MODEM_DUP_ID 0x0C
#define C_ORG_ERR_SYNTAX_H_SEQ 0x08
#define C_ORG_ERR_SYNTAX_LENGTH 0x09
#define C_ORG_ERR_SYNTAX_CHKSUM 0x0A
#define C_ORG_ERR_SYNTAX_ORG 0x0B
#define C_ORG_ERR_TX_IDRANGE 0x22
#define C_ORG_ERR_IDRANGE 0x1A
/*@}*/
/**
 * @defgroup other120 Other definitions for the TCM120-commands (TCT answers)
 * Other definitions for the command telegrams and messages for TCM 120. Used
 * for the answers of the TCM120 module.
 * @{
*/
/// Low receive sensitivity
#define C_RX_SENSITIVITY_LOW 0x00
/// High receive sensitivity
#define C_RX_SENSITIVITY_HIGH 0x01

/// Modem mode is on
#define C_MODEM_STATE_ON 0x01
/// Modem mode is off
#define C_MODEM_STATE_OFF 0x00
/*@}*/

/**
 * @defgroup TCM120_functions Functions for TCM120-commands
 * Functions for the construction of the TCM120-commands
 * @{
 */
/**
 * Construct the command to set the ID-base
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_set_idbase(BYTE baseByte0, BYTE baseByte1, BYTE baseByte2, BYTE baseByte3);
/**
 * Construct the request for the ID of the connected device.
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_rd_idbase();
/**
 * Construct the command to set the sensitivity
 * \param sensitivity The sensitivity low or high (see \ref other120)
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_set_rx_sensitivity(BYTE sensitivity);
/**
 * Construct the command to read the sensitivity
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_rd_rx_sensitivity();
/**
 * Construct the command to set the sleep mode
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_sleep();
/**
 * Construct the command to wake up after sleep
 * \return The byte of the command
 */
BYTE tcm120_wake();
/**
 * Construct the command to reset the module
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_reset();
/**
 * Construct the command to turn on modem mode
 * \param modemID_msb The MSB of the ModemID
 * \param modemID_lsb The LSB of the ModemID
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_modem_on(BYTE modemID_msb, BYTE modemID_lsb);
/**
 * Construct the command to turn off modem mode
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_modem_off();
/**
 * Construct the command to get the actual modem status
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_rd_modem_status();
/**
 * Construct the command to get the software version of the module
 * \return The datastructure (incl. checksum) of the command
 */
enocean_data_structure tcm120_rd_sw_ver();
/*@}*/

#endif /*TCM120_H_*/
