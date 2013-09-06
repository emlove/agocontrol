#ifndef TELEGRAM
#define TELEGRAM
 
#include <string>
#include <sstream>
#include <eibclient.h>

// some explanations

//this is a simple class to handle a message to send to/receive from the eibd program, through the librairy it provides
// a message is made of:
//		a group address to sen the message to
//		an address to know who sent the message. eibd sets it to 0, so not to manage
//		a message to send to the address. the encoding of the message is made according to the kind of device that is supposed to receive it.. and to the order we want to send
//		the length of the TOTAL frame, which is basically <data_length>+2

//	data type
//	there are frou types of data, we only manage 3:
//		EIBWRITE: tells to groupaddr to write the value in parameter
//		EIBREAD: ask to groupaddr its value
//		EIBRESPONSE: the response from a read
//		EIBMEMWRITE(not yet implemented / need moar doc)

//	data structure
//	the max total data length is 16
//		the start of the telegram is supposed to be 2 bytes representing the comamnd of the telegram
//		actually those orders are strored in bits 7,8,9,10 only.  bits 11-16 can be used for driving  some information: this is the shortuserdata
//		shortuserdata using and 'normal'datausing prevent each other. this is beacause shrotuserdata is only used when datalength is 0-this means, telegram data length is 2
//		since 2 bytes are used for the comamnd type the 'usefull' data is supposed to be between 0 and 14 bytes long.

//	groupaddress
//	there are thre ways to give a group address: you can have up to three 'separations'  on your group address
//		1 number: this number is converted as a nomral int on 2 bytes
//		2 numbers: first number represents the 5 upper bits; second number the remaining. separation in line/address
//		3 numbers: like before, but 2nd only represents the upper bits 6,7,8. so number 3 is the lower byte. this is line/group/address separation, the most commonly used

//	eibd
//	when sendig to eibd, you have to give:
//		groupaddress to send, with the type "eibaddr_t" which is a double char
//		data length. 2 + size of _data
//		dat buffer to copy from. this is char* .

#define MAXTELEGRAMDATALENGTH 14
#define MAXTELEGRAMLENGTH 16

using namespace std;

	enum TRAME_TYPE
	{
		EIBWRITE 	= 0x0080,
		EIBREAD		= 0x0000,
		EIBRESPONSE	= 0x0040,
		EIBMEMWRITE	= 0x0280
	};

	class Telegram
	{
		protected:
			char _data[MAXTELEGRAMLENGTH];
			int _length;
			int _shortdata;
			long int _type;
			eibaddr_t _addrdest;
			eibaddr_t _addrfrom;

		public:
			//default: creates a Telegram with write command, to addr 0, order 'off'
			Telegram();
			
			virtual ~Telegram(){};
			
			//set the group add of the telegram. must one of the types: "a/b/c" or "a/b" or "a", a,b,c being numbers.
			inline void setGroupAddress(string s){_addrdest= stringtogaddr(s);};
			inline void setGroupAddress(eibaddr_t addr){_addrdest=addr;};
			
			//set the shortuserdata(and thus sets the length to 0)
			void setShortUserData(short int sud);
			
			//set the data of the telegram to data, stores the length
			void setUserData(unsigned const char *data, int length);
			//set data from char
			void setDataFromChar(char c);
			//set data from float
			void setDataFromFloat(float f);
			
			
			//set the type of the telegram. keeps in memory data 
			void setType(long int type);
			
			//send the telegram on con
			bool sendTo(EIBConnection *con) const;

			bool receivefrom(EIBConnection *con);

			inline eibaddr_t getGroupAddress() const{return _addrdest;};
			inline eibaddr_t getSrcAddress() const{return _addrfrom;};

			inline int getShortUserData() const{return _shortdata;};

			//Acces to the data values.
			int getUserData(unsigned char *buffer, int maxsize) const;//return the sizeof data copied in buffer
			int getIntData() const;
			unsigned int getUIntData() const;
			float getFloatData() const;

			inline int getType() const{return _type;};

			string decodeType();

			//utilities

			//translates a string to its knx group address
			static eibaddr_t stringtogaddr(const string s);

			//and the reverse
			static string gaddrtostring(eibaddr_t addr);

			//translate "physical" adress to string
			static string paddrtostring(eibaddr_t addr);

			//translates  a short (2bytes) received from the knx bus to it's meaning in 'float'
			static float getFloatFromUShort(const unsigned short data);
		
			//reverse the previous: makes a knx 2Bytes short from a usual float;
			static unsigned short getUShortFromFloat(const float f );

		protected:
			inline int length(){return _length+2;};
			
			//regenerate the two bytes of the head
			void generate_head();
	};
 
#endif
