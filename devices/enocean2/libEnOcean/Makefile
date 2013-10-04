# CFLAGS=`pkg-config --cflags gtk+-2.0`
# LIBS=`pkg-config --libs gtk+-2.0`

all: EnOceanPortTest

cssl.o: cssl.h cssl.c
	gcc -c -D_GNU_SOURCE cssl.c

EnOceanPort.o: EnOceanPort.c EnOceanPort.h EnOceanProtocol.h TCM120.h
	gcc -c EnOceanPort.c

EnOceanPort: cssl.o EnOceanPort.o
	gcc -o"EnOceanPort" cssl.o EnOceanPort.o

EnOceanPortTest.o: EnOceanPortTest.c EnOceanProtocol.h EnOceanPort.h TCM120.h
	gcc -c EnOceanPortTest.c

EnOceanPortTest: EnOceanPort.o cssl.o EnOceanPortTest.o TCM120.o
	gcc -o"EnOceanPortTest" cssl.o EnOceanPort.o EnOceanPortTest.o TCM120.o

TCM120.o: TCM120.h TCM120.c EnOceanProtocol.h EnOceanPort.h
	gcc -c TCM120.c

dist:
	tar -czf enoceanlibrary-0.4.3.tar.gz COPYING COPYING.LESSER ChangeLog cssl.c cssl.h EnOceanPort.c EnOceanPort.h EnOceanPortTest.c EnOceanProtocol.h Makefile TCM120.c TCM120.h

clean:
	rm -f cssl.o EnOceanPort.o EnOceanPort EnOceanPortTest.o EnOceanPortTest TCM120.o
	rm -f *~
