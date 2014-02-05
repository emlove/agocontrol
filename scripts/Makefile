agososreport.sh: agososreport.sh.in
	sed -e 's|@CONFDIR|$(CONFDIR)|g' $< > $@

all: agososreport.sh

install:
	$(INSTALL_PROGRAM) agososreport.sh $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) convert-zwave-uuid.py $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) convert-scenario.py $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) convert-event.py $(DESTDIR)$(BINDIR)
	$(INSTALL_PROGRAM) convert-config.py $(DESTDIR)$(BINDIR)

clean:
	-rm agososreport.sh
