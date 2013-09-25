INCLUDES ?= -I../../shared
INCLUDES += -I/usr/include/jsoncpp
LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

all: agorpc cgi

agorpc: agorpc.o mongoose.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp -lagoclient

cgi:
	$(CXX) $(CFLAGS) -o html/cgi-bin/get_table_lang.cgi get_table_lang.cpp

clean:
	rm -f agorpc agorpc.o mongoose.o
	rm -f html/cgi-bin/get_table_lang.cgi
	find html/templates -name "*.html" | grep -v in.html | while read file ; do rm -v $$file ; done

install:
	( cd html ; ./mergetranslations.sh )
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL_PROGRAM) agorpc $(BINDIR)

