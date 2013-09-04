DIRS = resolver rpc messagesend timer scenario event manager

BUILDDIRS = $(DIRS:%=build-%)
INSTALLDIRS = $(DIRS:%=install-%)
CLEANDIRS = $(DIRS:%=clean-%)

all: $(BUILDDIRS)
$(DIRS): $(BUILDDIRS)
$(BUILDDIRS):
	$(MAKE) -C $(@:build-%=%)

install: $(INSTALLDIRS) all
	$(INSTALL_DIR) $(BINDIR)
	$(INSTALL) messagesend.py $(BINDIR)
	$(INSTALL) agodrain.py $(BINDIR)
	$(INSTALL) agoscenario.py $(BINDIR)
	$(INSTALL) agoevent.py $(BINDIR)
	$(INSTALL) boolParser.py $(BINDIR)
	$(INSTALL) myavahi.py $(BINDIR)
	$(INSTALL) agodatalogger.py $(BINDIR)
	$(INSTALL) agoctrl.sh $(BINDIR)

$(INSTALLDIRS): 
	$(MAKE) -C $(@:install-%=%) install

clean: $(CLEANDIRS)
$(CLEANDIRS): 
	$(MAKE) -C $(@:clean-%=%) clean

.PHONY: subdirs $(DIRS)
.PHONY: subdirs $(BUILDDIRS)
.PHONY: subdirs $(INSTALLDIRS)
.PHONY: subdirs $(CLEANDIRS)
.PHONY: all install clean
