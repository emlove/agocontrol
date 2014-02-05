LD = $(CXX)
INCLUDES ?= -I../../shared

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

command.lua : command.lua.in
	 sed -e 's|@CONFDIR|$(CONFDIR)|g' $< > $@

all: agolua command.lua

agolua: agolua.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -lagoclient -llua5.2

clean:
	rm -f agolua agolua.o command.lua

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agolua $(DESTDIR)$(BINDIR)
