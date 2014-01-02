LD = $(CXX)
INCLUDES	?= -I../../shared 
INCLUDES += -I/usr/include/openzwave -I/usr/include/openzwave/value_classes -I/usr/include/openzwave/platform -I/usr/include/openzwave/platform/unix

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agozwave

ifeq ($(uname_S),FreeBSD)
OS_LIBS=-lusb -liconv
else
OS_LIBS=-ludev
endif

agozwave: agozwave.o ZWaveNode.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient -lopenzwave $(OS_LIBS)

clean:
	rm -f agozwave agozwave.o ZWaveNode.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agozwave $(BINDIR)
	$(INSTALL_DIR) $(CONFDIR)
	$(INSTALL_DIR) $(CONFDIR)/ozw

