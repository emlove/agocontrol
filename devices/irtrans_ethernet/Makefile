LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoirtrans_ethernet

agoirtrans_ethernet: agoirtrans_ethernet.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agoirtrans_ethernet agoirtrans_ethernet.o 

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agoirtrans_ethernet $(DESTDIR)$(BINDIR)
