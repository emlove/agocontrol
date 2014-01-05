LD = $(CXX)

INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agosecurity

agosecurity: agosecurity.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -lagoclient

.PHONY: clean
clean:
	rm -f agosecurity.o agosecurity

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agosecurity $(BINDIR)
