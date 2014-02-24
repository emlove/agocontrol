LIB_VER         := .1
LD = $(CXX)
CFLAGS	+= -fpic
LDFLAGS += -shared -Wl,-soname,libagoclient.so$(LIB_VER)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) -o $@ $<

all: libagoclient.so agoclient.py

libagoclient.so: agoclient.h agoclient.o CDataFile.o
	$(LD) -o $(@)$(LIB_VER) $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp
	test -h $(@) || ln -s $(@)$(LIB_VER) $(@)

agoclient.py: agoclient.py.in
	sed -e 's|@BINDIR@|$(BINDIR)|g' \
		-e 's|@CONFDIR@|$(CONFDIR)|g' $< > $@

agoclient.h: agoclient.h.in
	sed -e 's|@BINDIR@|$(BINDIR)|g' \
		-e 's|@CONFDIR@|$(CONFDIR)|g' \
		-e 's|@LOCALSTATEDIR@|$(LOCALSTATEDIR)|g' \
		-e 's|@HTMLDIR@|$(HTMLDIR)|g' $< > $@

clean:
	rm -f agoclient.h agoclient.o CDataFile.o libagoclient.so* agoclient.py

install:
	$(INSTALL) -d $(DESTDIR)$(LIBDIR)
	$(INSTALL) -d $(DESTDIR)$(BINDIR)
	$(INSTALL) -d $(DESTDIR)$(INCDIR)
	$(INSTALL) libagoclient.so.1 $(DESTDIR)$(LIBDIR)
	$(INSTALL) agoclient.py $(DESTDIR)$(BINDIR)
	$(INSTALL) agoclient.h $(DESTDIR)$(INCDIR)
	$(INSTALL) CDataFile.h $(DESTDIR)$(INCDIR)
