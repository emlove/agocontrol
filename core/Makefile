DIRS = resolver rpc messagesend timer scenario event manager datalogger

BUILDDIRS = $(DIRS:%=build-%)
INSTALLDIRS = $(DIRS:%=install-%)
CLEANDIRS = $(DIRS:%=clean-%)

agocontrol-init-script.sh: agocontrol-init-script.sh.in
	sed -e 's|@BINDIR@|$(BINDIR)|g' $< > $@

all: agocontrol-init-script.sh $(BUILDDIRS)
$(DIRS): $(BUILDDIRS)
$(BUILDDIRS):
	$(MAKE) -C $(@:build-%=%)

install: $(INSTALLDIRS) all
	$(INSTALL_DIR) $(DESTDIR)$(BINDIR)
	$(INSTALL) agodrain.py $(DESTDIR)$(BINDIR)
	$(INSTALL) myavahi.py $(DESTDIR)$(BINDIR)
	$(INSTALL) agoctrl.sh $(DESTDIR)$(BINDIR)

$(INSTALLDIRS): 
	$(MAKE) -C $(@:install-%=%) install

clean: $(CLEANDIRS)
	rm agocontrol-init-script.sh

$(CLEANDIRS): 
	$(MAKE) -C $(@:clean-%=%) clean

.PHONY: subdirs $(DIRS)
.PHONY: subdirs $(BUILDDIRS)
.PHONY: subdirs $(INSTALLDIRS)
.PHONY: subdirs $(CLEANDIRS)
.PHONY: all install clean
