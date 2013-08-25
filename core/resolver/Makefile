%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoresolver

agoresolver: agoresolver.o schema.o inventory.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lyaml-cpp  -lsqlite3 -lagoclient

clean:
	rm -f agoresolver agoresolver.o schema.o inventory.o

install:
	$(INSTALL) agoresolver $(BINDIR)
