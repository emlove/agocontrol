#ifndef ESP3_H
#define ESP3_H

#define ESP3_SYNC 0x55
#define ESP3_HEADER_LENGTH 0x4

namespace esp3 {

typedef enum {
	RORG_RPS = 0xF6,
	RORG_1BS = 0xD5,
	RORG_4BS = 0xA5,
	RORG_VLD = 0xD2,
	RORG_MSC = 0xD1,
	RORG_ADT = 0xA6,
	RORG_SM_LRN_REQ = 0xC6,
	RORG_SM_LRN_ANS = 0xC7, 
	RORG_SM_REC = 0xA7,
	RORG_SYS_EX = 0xC5
} ESP3_RORG;

const uint8_t crc8table[256] = { 0x00, 0x07, 0x0e, 0x09, 0x1c, 0x1b, 0x12, 0x15, 0x38, 0x3f, 0x36, 0x31, 0x24, 0x23, 0x2a, 0x2d, 0x70, 0x77, 0x7e, 0x79, 0x6c, 0x6b, 0x62, 0x65, 0x48, 0x4f, 0x46, 0x41, 0x54, 0x53, 0x5a, 0x5d, 0xe0, 0xe7, 0xee, 0xe9, 0xfc, 0xfb, 0xf2, 0xf5, 0xd8, 0xdf, 0xd6, 0xd1, 0xc4, 0xc3, 0xca, 0xcd, 0x90, 0x97, 0x9e, 0x99, 0x8c, 0x8b, 0x82, 0x85, 0xa8, 0xaf, 0xa6, 0xa1, 0xb4, 0xb3, 0xba, 0xbd,  0xc7, 0xc0, 0xc9, 0xce, 0xdb, 0xdc, 0xd5, 0xd2, 0xff, 0xf8, 0xf1, 0xf6, 0xe3, 0xe4, 0xed, 0xea, 0xb7, 0xb0, 0xb9, 0xbe, 0xab, 0xac, 0xa5, 0xa2, 0x8f, 0x88, 0x81, 0x86, 0x93, 0x94, 0x9d, 0x9a, 0x27, 0x20, 0x29, 0x2e, 0x3b, 0x3c, 0x35, 0x32, 0x1f, 0x18, 0x11, 0x16, 0x03, 0x04, 0x0d, 0x0a, 0x57, 0x50, 0x59, 0x5e, 0x4b, 0x4c, 0x45, 0x42, 0x6f, 0x68, 0x61, 0x66, 0x73, 0x74, 0x7d, 0x7a, 0x89, 0x8e, 0x87, 0x80, 0x95, 0x92, 0x9b, 0x9c, 0xb1, 0xb6, 0xbf, 0xb8, 0xad, 0xaa, 0xa3, 0xa4, 0xf9, 0xfe, 0xf7, 0xf0, 0xe5, 0xe2, 0xeb, 0xec, 0xc1, 0xc6, 0xcf, 0xc8, 0xdd, 0xda, 0xd3, 0xd4, 0x69, 0x6e, 0x67, 0x60, 0x75, 0x72, 0x7b, 0x7c, 0x51, 0x56, 0x5f, 0x58, 0x4d, 0x4a, 0x43, 0x44, 0x19, 0x1e, 0x17, 0x10, 0x05, 0x02, 0x0b, 0x0c, 0x21, 0x26, 0x2f, 0x28, 0x3d, 0x3a, 0x33, 0x34, 0x4e, 0x49, 0x40, 0x47, 0x52, 0x55, 0x5c, 0x5b, 0x76, 0x71, 0x78, 0x7f, 0x6A, 0x6d, 0x64, 0x63, 0x3e, 0x39, 0x30, 0x37, 0x22, 0x25, 0x2c, 0x2b, 0x06, 0x01, 0x08, 0x0f, 0x1a, 0x1d, 0x14, 0x13, 0xae, 0xa9, 0xa0, 0xa7, 0xb2, 0xb5, 0xbc, 0xbb, 0x96, 0x91, 0x98, 0x9f, 0x8a, 0x8D, 0x84, 0x83, 0xde, 0xd9, 0xd0, 0xd7, 0xc2, 0xc5, 0xcc, 0xcb, 0xe6, 0xe1, 0xe8, 0xef, 0xfa, 0xfd, 0xf4, 0xf3 }; 

#define proc_crc8(crc, data) (crc8table[crc ^ data])

typedef uint8_t uint8;
typedef uint16_t uint16;
// the following lines are taken from EO300I API header file

#define SER_SYNCH_CODE 0x55
#define SER_HEADER_NR_BYTES 0x04

//! Packet structure (ESP3)
typedef struct
{
	uint16	u16DataLength;	         //! Amount of raw data bytes to be received. The most significant byte is sent/received first
	uint8	u8OptionLength;			 //! Amount of optional data bytes to be received
	uint8	u8Type;					 //! Packe type code
	uint8	*u8DataBuffer;			 //! Packe type code

} PACKET_SERIAL_TYPE;

//! Packet type (ESP3)
typedef enum
{
	PACKET_RESERVED 			= 0x00,	//! Reserved
	PACKET_RADIO 				= 0x01,	//! Radio telegram
	PACKET_RESPONSE				= 0x02,	//! Response to any packet
	PACKET_RADIO_SUB_TEL		= 0x03,	//! Radio subtelegram (EnOcean internal function )
	PACKET_EVENT 				= 0x04,	//! Event message
	PACKET_COMMON_COMMAND 		= 0x05,	//! Common command
	PACKET_SMART_ACK_COMMAND	= 0x06,	//! Smart Ack command
	PACKET_REMOTE_MAN_COMMAND	= 0x07,	//! Remote management command
	PACKET_PRODUCTION_COMMAND	= 0x08,	//! Production command
	PACKET_RADIO_MESSAGE		= 0x09,	//! Radio message (chained radio telegrams)
	PACKET_RADIO_ADVANCED		= 0x0a  //! Advanced Protocol radio telegram

} PACKET_TYPE;

//! Response type
typedef enum
{
	RET_OK 					= 0x00, //! OK ... command is understood and triggered
	RET_ERROR 				= 0x01, //! There is an error occured
	RET_NOT_SUPPORTED 		= 0x02, //! The functionality is not supported by that implementation
	RET_WRONG_PARAM 		= 0x03, //! There was a wrong parameter in the command
	RET_OPERATION_DENIED 	= 0x04, //! Example: memory access denied (code-protected)
	RET_USER				= 0x80	//! Return codes greater than 0x80 are used for commands with special return information, not commonly useable.
} RESPONSE_TYPE;

//! Common command enum
typedef enum
{
	CO_WR_SLEEP			= 1,	//! Order to enter in energy saving mode
	CO_WR_RESET			= 2,	//! Order to reset the device
	CO_RD_VERSION		= 3,	//! Read the device (SW) version / (HW) version, chip ID etc.
	CO_RD_SYS_LOG		= 4,	//! Read system log from device databank
	CO_WR_SYS_LOG		= 5,	//! Reset System log from device databank
	CO_WR_BIST			= 6,	//! Perform Flash BIST operation
	CO_WR_IDBASE		= 7,	//! Write ID range base number
	CO_RD_IDBASE		= 8,	//! Read ID range base number
	CO_WR_REPEATER		= 9,	//! Write Repeater Level off,1,2
	CO_RD_REPEATER		= 10,	//! Read Repeater Level off,1,2
	CO_WR_FILTER_ADD	= 11,	//! Add filter to filter list
	CO_WR_FILTER_DEL	= 12,	//! Delete filter from filter list
	CO_WR_FILTER_DEL_ALL= 13,	//! Delete filters
	CO_WR_FILTER_ENABLE	= 14,	//! Enable/Disable supplied filters
	CO_RD_FILTER		= 15,	//! Read supplied filters
	CO_WR_WAIT_MATURITY	= 16,	//! Waiting till end of maturity time before received radio telegrams will transmitted
	CO_WR_SUBTEL		= 17,	//! Enable/Disable transmitting additional subtelegram info
	CO_WR_MEM			= 18,	//! Write x bytes of the Flash, XRAM, RAM0 ….
	CO_RD_MEM			= 19,	//! Read x bytes of the Flash, XRAM, RAM0 ….
	CO_RD_MEM_ADDRESS	= 20,	//! Feedback about the used address and length of the config area and the Smart Ack Table
	CO_RD_SECURITY		= 21,	//! Read security informations (level, keys)
	CO_WR_SECURITY		= 22,	//! Write security informations (level, keys)
} COMMON_COMMAND_TYPE; 

//! Function return codes
typedef enum
{
	//! <b>0</b> - Action performed. No problem detected
	OK=0,							
	//! <b>1</b> - Action couldn't be carried out within a certain time.  
	TIME_OUT,		
	//! <b>2</b> - The write/erase/verify process failed, the flash page seems to be corrupted
	FLASH_HW_ERROR,				
	//! <b>3</b> - A new UART/SPI byte received
	NEW_RX_BYTE,				
	//! <b>4</b> - No new UART/SPI byte received	
	NO_RX_BYTE,					
	//! <b>5</b> - New telegram received
	NEW_RX_TEL,	  
	//! <b>6</b> - No new telegram received
	NO_RX_TEL,	  
	//! <b>7</b> - Checksum not valid
	NOT_VALID_CHKSUM,
	//! <b>8</b> - Telegram not valid  
	NOT_VALID_TEL,
	//! <b>9</b> - Buffer full, no space in Tx or Rx buffer
	BUFF_FULL,
	//! <b>10</b> - Address is out of memory
	ADDR_OUT_OF_MEM,
	//! <b>11</b> - Invalid function parameter
	NOT_VALID_PARAM,
	//! <b>12</b> - Built in self test failed
	BIST_FAILED,
	//! <b>13</b> - Before entering power down, the short term timer had timed out.	
	ST_TIMEOUT_BEFORE_SLEEP,
	//! <b>14</b> - Maximum number of filters reached, no more filter possible
	MAX_FILTER_REACHED,
	//! <b>15</b> - Filter to delete not found
	FILTER_NOT_FOUND,
	//! <b>16</b> - BaseID out of range
	BASEID_OUT_OF_RANGE,
	//! <b>17</b> - BaseID was changed 10 times, no more changes are allowed
	BASEID_MAX_REACHED,
	//! <b>18</b> - XTAL is not stable
	XTAL_NOT_STABLE,
	//! <b>19</b> - No telegram for transmission in queue  
	NO_TX_TEL,
	//!	<b>20</b> - Waiting before sending broadcast message
	TELEGRAM_WAIT,
	//!	<b>21</b> - Generic out of range return code
	OUT_OF_RANGE,
	//!	<b>22</b> - Function was not executed due to sending lock
	LOCK_SET,
	//! <b>23</b> - New telegram transmitted
	NEW_TX_TEL
} RETURN_TYPE;
// end of lines from EO300I API header file


	class ESP3 {
		public:
			ESP3(std::string _devicefile);
			~ESP3();
			bool init();
			void *readerFunction();
			uint32_t getIdBase();
			bool fourbsCentralCommandDimLevel(uint16_t rid, uint8_t level, uint8_t speed);
			bool fourbsCentralCommandDimOff(uint16_t rid);
			bool fourbsCentralCommandDimTeachin(uint16_t rid);
			bool fourbsCentralCommandSwitchOn(uint16_t rid);
			bool fourbsCentralCommandSwitchOff(uint16_t rid);
			bool fourbsCentralCommandSwitchTeachin(uint16_t rid);
		private:
			int readFrame(uint8_t *buf, int &datasize, int &optdatasize);
			void parseFrame(uint8_t *buf, int datasize, int optdatasize);
			bool sendFrame(uint8_t frametype, uint8_t *databuf, uint16_t datalen, uint8_t *optdata, uint8_t optdatalen);
			bool readIdBase();

			uint32_t idBase;
			std::string devicefile;
			int fd;
			pthread_t eventThread;
			pthread_mutex_t serialMutex;

	};

}

#endif
