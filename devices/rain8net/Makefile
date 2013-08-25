LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agorain8net

agorain8net: agorain8net.o rain8.o serial.o 
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agorain8net rain8.o serial.o agorain8net.o 

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agorain8net $(BINDIR)
