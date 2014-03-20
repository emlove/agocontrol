INCLUDES += -I../../

LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoresolver

agoresolver: agoresolver.o schema.o inventory.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lyaml-cpp  -lsqlite3 -lagoclient

test:
	$(CXX) $(CFLAGS) $(INCLUDES) -DINVENTORY_TEST -o inventorytest inventory.cpp  -lsqlite3  -lqpidtypes 

clean:
	rm -f agoresolver agoresolver.o schema.o inventory.o

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agoresolver $(DESTDIR)$(BINDIR)
