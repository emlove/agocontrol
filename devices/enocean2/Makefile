LD = $(CXX)

INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c  $(CFLAGS) $(INCLUDES) -o $@ $<

all: enoceanlib agoEnOcean

enoceanlib:
	$(CC) -c -fPIC -D_GNU_SOURCE -o cssl.o libEnOcean/cssl.c
	$(CC) -c -fPIC -o EnOceanPort.o libEnOcean/EnOceanPort.c
	$(CC) -c -fPIC -o TCM120.o libEnOcean/TCM120.c

agoEnOcean: agoEnOcean.o
	$(LD) -o $@ cssl.o EnOceanPort.o TCM120.o $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agoEnOcean agoEnOcean.o TCM120.o EnOceanPort.o cssl.o

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agoEnOcean $(DESTDIR)$(BINDIR)
