SOAPOBJ=soapC.o stdsoap2.o soapMediaBindingProxy.o wsseapi.o mecevp.o smdevp.o threads.o dom.o wsaapi.o soapDeviceBindingProxy.o duration.o soapwsddProxy.o
LIBS=-L../../shared -luuid -lssl -lagoclient 
INCLUDES=-I../gsoap-2.8/gsoap/plugin/ -I. -I/usr/include -I../../shared 
DEFINES=-DWITH_DOM -DWITH_OPENSSL -DDEBUG

%.o:%.cpp
	g++ -g -c $< $(INCLUDES) $(DEFINES)
%.o:%.c
	gcc -g -c $< $(INCLUDES) $(DEFINES)

all:	agoonvif

agoonvif: $(SOAPOBJ) onvif.o
	g++ -g  onvif.o $(SOAPOBJ) $(LIBS) -o agoonvif 

clean:
	rm -f agoonvif *.o | tee
