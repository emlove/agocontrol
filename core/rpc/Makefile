INCLUDES ?= -I../../shared
INCLUDES += -I/usr/include/jsoncpp
LD = $(CXX)

%.o : %.cpp
	$(CXX) -c $(CFLAGS) $(INCLUDES) -o $@ $<

%.html : %.in.html
	./mergetranslation.sh $< $@

all: agorpc html cgi

agorpc: agorpc.o mongoose.o
	$(LD) -o $@ $(LDFLAGS) $^ -lqpidmessaging -lqpidtypes -luuid -ljsoncpp -lagoclient

html: $(patsubst %.in.html,%.html,$(wildcard html/templates/*.in.html) $(wildcard html/templates/details/*.in.html) $(wildcard html/templates/devices/*.in.html) $(wildcard html/templates/configuration/*.in.html) $(wildcard html/templates/navigation/*.in.html))

cgi:  get_table_lang.cpp
	$(CXX) $(CFLAGS) -o html/cgi-bin/get_table_lang.cgi get_table_lang.cpp
	sed -e 's|@BINDIR@|$(BINDIR)|g' activate.cgi.in > html/cgi-bin/activate.cgi

clean:
	rm -f agorpc agorpc.o mongoose.o
	rm -f html/cgi-bin/get_table_lang.cgi
	rm -f html/cgi-bin/activate.cgi
	find html/templates -name "*.html" | grep -v in.html | while read file ; do rm -v $$file ; done

install:
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) agorpc $(DESTDIR)$(BINDIR)

