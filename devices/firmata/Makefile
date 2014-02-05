LD = $(CXX)
INCLUDES ?= -I../../shared
INCLUDES += "-I."

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agofirmata

agofirmata: agofirmata.o firmata.o arduino.o 
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agofirmata firmata.o arduino.o agofirmata.o 

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agofirmata $(DESTDIR)$(BINDIR)
