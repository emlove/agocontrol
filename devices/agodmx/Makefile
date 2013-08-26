LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agodmx


agodmx: agodmx.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ltinyxml2 -lagoclient -lola -lolacommon

clean:
	rm -f agodmx agodmx.o 

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agodmx $(BINDIR)
