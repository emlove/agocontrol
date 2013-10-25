LIB_VER         := .1
LD = $(CXX)
CFLAGS	+= -fpic
LDFLAGS += -shared -Wl,-soname,libagoclient.so$(LIB_VER)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) -o $@ $<

all: libagoclient.so

libagoclient.so: agoclient.o CDataFile.o
	$(LD) -o $(@)$(LIB_VER) $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp
	test -h $(@) || ln -s $(@)$(LIB_VER) $(@)

clean:
	rm -f agoclient.o CDataFile.o libagoclient.so*

install:
	$(INSTALL) -d $(DESTDIR)$(LIBDIR)
	$(INSTALL) -d $(DESTDIR)$(BINDIR)
	$(INSTALL) -d $(DESTDIR)$(INCDIR)
	$(INSTALL) libagoclient.so.1 $(DESTDIR)$(LIBDIR)
	$(INSTALL) agoclient.py $(DESTDIR)$(BINDIR)
	$(INSTALL) agoclient.h $(DESTDIR)$(INCDIR)
