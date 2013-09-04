LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoevent

agoevent: agoevent.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lagoclient

clean:
	rm -f agoevent agoevent.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agoevent $(BINDIR)
