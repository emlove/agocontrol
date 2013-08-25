INCLUDES ?= -I../../shared
LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: messagesend

messagesend: messagesend.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient

clean:
	rm -f messagesend messagesend.o

install:
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) messagesend $(BINDIR)

