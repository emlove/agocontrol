LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoi2c

agoi2c: agoi2c.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient 

clean:
	rm -f agoi2c  agoi2c.o

install:
	$(INSTALL) agoi2c $(BINDIR)
