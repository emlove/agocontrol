INCLUDES ?= -I../../shared
LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: messagesend

messagesend: messagesend.o
	$(LD) -o $@ $(LDFLAGS) $^ -lagoclient -lqpidtypes

clean:
	rm -f messagesend messagesend.o

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) messagesend $(DESTDIR)$(BINDIR)
