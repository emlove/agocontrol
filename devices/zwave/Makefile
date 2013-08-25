LD = $(CXX)
INCLUDES	?= -I../../shared 
INCLUDES += -I/usr/include/openzwave -I/usr/include/openzwave/value_classes -I/usr/include/openzwave/platform -I/usr/include/openzwave/platform/unix

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agozwave

agozwave: agozwave.o ZWaveNode.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient -lopenzwave -ludev

clean:
	rm -f agozwave agozwave.o ZWaveNode.o

install:
	$(INSTALL) agozwave $(BINDIR)
	$(INSTALL) -d $(CONFDIR)/ozw

