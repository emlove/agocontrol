
#include "Telegram.h"
#include "math.h"

Telegram::Telegram():_length(0),_shortdata(0),_type(EIBWRITE),_addrdest(0),_addrfrom(0)
{
	for(int i=0;i<MAXTELEGRAMLENGTH;i++)
	{
		_data[i]=0;
	}
}

void Telegram::setShortUserData(short int sud)
{
	//no data for READ command
	if(_type==EIBREAD) return;
	_length=0;
	_shortdata=sud;
	generate_head();
}

void Telegram::setUserData(const unsigned char *data, int length)
{
	//no data for READ command
	if(_type==EIBREAD) return;
	_shortdata=0;
	
	_length=length=(length>MAXTELEGRAMDATALENGTH-2?MAXTELEGRAMDATALENGTH-2:length);
	for(int i=0;i<length;i++)
	{
		_data[i+2]=data[i];
	}
	generate_head();
}

void Telegram::setDataFromChar(char c)
{
	setUserData((unsigned char *)&c,1);
}

void Telegram::setDataFromFloat(float f)
{
	unsigned short sf = getUShortFromFloat(f);
	setUserData((unsigned char*)&sf, sizeof(sf));
}

void Telegram::setType(long int type)
{
	if(type!=EIBREAD && type!=EIBWRITE) throw string("error: unavailable command to EIB telegramm");
	if(_type==type) return;
	_type=type;
	generate_head();
}


bool Telegram::sendTo(EIBConnection *con) const
{
	return(EIBSendGroup (con, _addrdest, _length+2, (const uint8_t *)_data)>-1);
}

bool Telegram::receivefrom(EIBConnection *con)
{
	int len;
	eibaddr_t dest;
	eibaddr_t src;
	uint8_t buf[MAXTELEGRAMLENGTH];
	len = EIBGetGroup_Src (con, sizeof (buf), buf, &src, &dest);
	if (len<2) return false;
	_type = ((buf[0] & 0x3)<<8) | (buf[1] & 0xc0) ;
	if(_type!=EIBWRITE && _type!=EIBREAD && _type!=EIBRESPONSE) return false;
	_length=len-2;
	_addrfrom=src; _addrdest=dest;
	if(_length==0) _shortdata=buf[1] & 0x3f;
	for (int i=0;i<_length;i++) _data[i]=buf[i+2];
	return true;
}

int Telegram::getUserData(unsigned char *buffer, int maxsize) const
{
	int leng=(maxsize<_length?maxsize:_length);
	for(int i =0;i<leng;i++) buffer[i]=_data[i];
	return leng;
}

unsigned int Telegram::getUIntData() const
{

	switch(_length)
	{
		case(0): return _shortdata; break;
		case(1): return (int)*(unsigned char*)_data;break;
		case(2): return ( (int)(unsigned char)_data[0] <<8 )  + (int)(unsigned char)_data[1];
		default: return 0;
	}

}
int Telegram::getIntData() const
{
	switch(_length)
	{
		case(0): return _shortdata; break;
		case(1): return (int)*_data;break;
		case(2): return ( (int)_data[0] <<8 )  + (int)_data[1];
		default: return 0;
	}
}

float Telegram::getFloatData() const
{
	switch(_length)
	{
		case(0):
		
		case(1): 
			return 0.0;
			break;
		
		case(2):
			unsigned short usd;
			getUserData((unsigned char*)&usd,2);
			return getFloatFromUShort(usd);
			break;
			
		default: return 0;
	}
	
}

eibaddr_t  Telegram::stringtogaddr(const string s)
{
	unsigned int a[3]={0};
	int nbslash=0;
	for(int i=0;s[i]!='\0'&&nbslash<3;i++)
	{
		if(s[i]=='/')
		{
			nbslash++;
		}else{
			a[nbslash]=a[nbslash]*10+s[i]-'0';
		}
	}
	switch(nbslash)
	{
		case(0): return (a[0] & 0xffff);break;
		case(1): return ((a[0] & 0x01f) << 11) | ((a[1] & 0x7FF)); ;break;
		case(2): return ((a[0] & 0x01f) << 11) | ((a[1] & 0x007) << 8 ) | (a[2] & 0x0ff) ;break;
		default: throw string("error parsing the groupaddr");
	}
}

string Telegram::gaddrtostring(eibaddr_t addr)
{
	int a = addr>>11;
	int b = (addr>>8) & 0x7;
	int c = addr & 0xff;
	ostringstream oa; oa << a;
	ostringstream ob; ob << b;
	ostringstream oc; oc << c;
	string sa=oa.str(), sb=ob.str(), sc=oc.str();
	string s("/");
	return sa+s+sb+s+sc;
}

string Telegram::paddrtostring(eibaddr_t addr)
{
	int a = addr>>12;
	int b = (addr>>8) & 0xf;
	int c = addr & 0xff;
	ostringstream oa; oa << a;
	ostringstream ob; ob << b;
	ostringstream oc; oc << c;
	string sa=oa.str(), sb=ob.str(), sc=oc.str();
	string s("/");
	return sa+s+sb+s+sc;
}

string Telegram::decodeType()
{
	switch(_type)
	{
		case(EIBREAD)		: return string("read");break;
		case(EIBWRITE)		: return string("write");break;
		case(EIBRESPONSE)	: return string("response");break;
		case(EIBMEMWRITE)	: return string("memwrite");break;
		default:return string("undefined");
	}
}

float Telegram::getFloatFromUShort(unsigned short tempr)
{
	// change bytes
	unsigned short byte0 = tempr & 0x00ff, byte1 = (tempr & 0xff00 ) >> 8;
	tempr = (byte0 << 8)+ byte1;
	
	int sign = ((tempr & 0x8000) != 0) ? 1 : 0;  // last bit
	int exponent = (tempr & 0x7800) >> 11;
	
	int pow = 1;
	for( int i = 0; i < exponent; i++ )
		pow *= 2;
	
	int mantissa = tempr & 0x07ff;
	if( sign == 1 ) // two's complement
	{
		mantissa ^= 0x7ff;
		mantissa += 1;
		mantissa &= 0x07ff;
	}
	
	int result = pow * mantissa;
	if( sign == 1 ) {
		result = (-result);
	}

	return (1.0) * result / 100;
}

unsigned short Telegram::getUShortFromFloat( float tempr )
{
	int sign = 0;
	if(tempr < 0) {
		sign = 1;
		tempr = -tempr;
	}
	
	/*calculate mantisa*/
	float fmantissa = tempr * 100;
	int exponent = 0;
	while(fmantissa > 2047) {
		fmantissa /=  2;
		exponent += 1;
	}
	int mantissa = (int)fmantissa;
	if( sign ) { // two's complement
		mantissa -= 1;
		mantissa ^= 0x7ff;
	}
	
	unsigned short ret = mantissa + (exponent << 11) + (sign << 15);
	
	// change bytes
	unsigned short byte0 = ret & 0x00ff, byte1 = (ret & 0xff00 ) >> 8;
	return ((byte0 << 8) + byte1);
}

void Telegram::generate_head()
{
	_data[0]=(_type>>8) & 0x3;

	if(_type==EIBWRITE && _length==0)
	{
		_data[1]=(_type & 0xff) | (_shortdata & 0x3f);
	}else{
		_data[1]=_type & 0xff;
	}
}
