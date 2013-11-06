LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoevent

agoevent: agoevent.o bool.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lagoclient

booltest:
	$(CXX) -c $(CFLAGS) $(INCLUDES) -DBOOLTEST -o booltest.o bool.cpp
	$(LD) -o $@ $(LDFLAGS) booltest.o -lboost_system

clean:
	rm -f agoevent agoevent.o booltest booltest.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agoevent $(BINDIR)
