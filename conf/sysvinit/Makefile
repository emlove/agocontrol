FILES = agocontrol

agocontrol : agocontrol.in
	sed -e 's|@BINDIR@|$(BINDIR)|g' $< > $@

all: $(FILES)

install:
#	$(INSTALL_DIR) $(DESTDIR)$(ETCDIR)/init.d
#	$(INSTALL_FILE) agocontrol $(DESTDIR)$(ETCDIR)/init.d

clean:
	-rm $(FILES)
