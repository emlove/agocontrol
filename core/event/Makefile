LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

ifeq ($(uname_S),FreeBSD)
BOOST_SYSTEM+=-lboost_system
else
BOOST_SYSTEM+=-l:libboost_system.so.1.49.0
endif
LIBS=$(BOOST_SYSTEM) -lqpidmessaging -lqpidtypes -luuid -lagoclient

all: agoevent

agoevent: agoevent.o bool.o
	$(LD) -o $@ $(LDFLAGS) $^ $(LIBS)

booltest:
	$(CXX) -c $(CFLAGS) $(INCLUDES) -DBOOLTEST -o booltest.o bool.cpp
	$(LD) -o $@ $(LDFLAGS) booltest.o $(BOOST_SYSTEM)

clean:
	rm -f agoevent agoevent.o booltest booltest.o bool.o

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agoevent $(DESTDIR)$(BINDIR)
