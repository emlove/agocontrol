LD = $(CXX)

INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c  $(CFLAGS) $(INCLUDES) -o $@ $<

all: agoenocean3

agoenocean3: agoenocean3.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f agoenocean3 agoenocean3.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agoenocean3 $(BINDIR)
