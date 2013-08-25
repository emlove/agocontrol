LD = $(CXX)

INCLUDES ?=  -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoknx

agoknx: agoknx.o Telegram.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -leibclient -ltinyxml2 -lagoclient

clean:
	rm -f agoknx agoknx.o Telegram.o

install:
	$(INSTALL) agoknx $(BINDIR)
