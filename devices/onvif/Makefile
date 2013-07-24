SOAPOBJ=soapC.o stdsoap2.o soapClient.o
LIBS=-luuid

onvif: $(SOAPOBJ) onvif.o
	g++  onvif.o $(SOAPOBJ) $(LIBS) -o onvif

clean:
	rm onvif
