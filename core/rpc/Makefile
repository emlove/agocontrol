INCLUDES ?= -I../../shared
INCLUDES += -I/usr/include/jsoncpp
LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agorpc

agorpc: agorpc.o mongoose.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp -lagoclient

clean:
	rm -f agorpc agorpc.o mongoose.o

install:
	$(INSTALL) agorpc $(BINDIR)

