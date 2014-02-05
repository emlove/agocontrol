LD = $(CXX)

INCLUDES ?=  -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agowebcam

agowebcam: agowebcam.o base64.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -lagoclient -lcurl

clean:
	rm -f agowebcam agowebcam.o base64.o

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agowebcam $(DESTDIR)$(BINDIR)
