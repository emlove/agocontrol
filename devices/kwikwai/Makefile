LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c  $(CFLAGS) $(INCLUDES) -o $@ $<

all: agokwikwai

agokwikwai: agokwikwai.o kwikwai.o 
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agokwikwai agokwikwai.o kwikwai.o

install:
	$(INSTALL) agokwikwai $(BINDIR)
