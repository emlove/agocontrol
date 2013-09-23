INCLUDES ?= -I../../shared
INCLUDES += -I/usr/include/jsoncpp
LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agorpc translations

agorpc: agorpc.o mongoose.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp -lagoclient

translations:
	$(MAKE) -C html

clean:
	$(MAKE) -C html clean
	rm -f agorpc agorpc.o mongoose.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agorpc $(BINDIR)

