LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agolua

agolua: agolua.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lagoclient -llua5.2

clean:
	rm -f agolua agolua.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agolua $(BINDIR)
