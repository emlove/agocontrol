LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agodatalogger

agodatalogger: agodatalogger.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lagoclient -lsqlite3

clean:
	rm -f agodatalogger agodatalogger.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agodatalogger $(BINDIR)
