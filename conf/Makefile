DIRS = systemd conf.d

# Generate a list of all .init files that need to be created
FILES = $(patsubst %.init.in, %.init, $(wildcard *.init.in))

BUILDDIRS = $(DIRS:%=build-%)
INSTALLDIRS = $(DIRS:%=install-%)
CLEANDIRS = $(DIRS:%=clean-%)

%.init : %.init.in
	sed -e 's|@BINDIR|$(BINDIR)|g' $< > $@

all: $(BUILDDIRS) $(FILES)
$(DIRS): $(BUILDDIRS)
$(BUILDDIRS):
	$(MAKE) -C $(@:build-%=%)

install: $(INSTALLDIRS) all
$(INSTALLDIRS): 
	install -d $(DESTDIR)$(CONFDIR)/db
	install -d $(DESTDIR)$(CONFDIR)/old
	install -d $(DESTDIR)$(CONFDIR)/rpc
	install -d $(DESTDIR)$(CONFDIR)/uuidmap
	install -d $(DESTDIR)$(CONFDIR)/maps
	install -d $(DESTDIR)$(ETCDIR)/sysctl.d
	install -d $(DESTDIR)$(ETCDIR)/security/limits.d
	install security-limits.conf $(DESTDIR)$(ETCDIR)/security/limits.d/agocontrol.conf
	install sysctl.conf $(DESTDIR)$(ETCDIR)/sysctl.d/agocontrol.conf
	install schema.yaml $(DESTDIR)$(CONFDIR)
	install rpc_cert.pem $(DESTDIR)$(CONFDIR)/rpc
	$(MAKE) -C $(@:install-%=%) install

clean: $(CLEANDIRS)
$(CLEANDIRS): 
	$(MAKE) -C $(@:clean-%=%) clean
	-rm $(FILES)

.PHONY: subdirs $(DIRS)
.PHONY: subdirs $(BUILDDIRS)
.PHONY: subdirs $(INSTALLDIRS)
.PHONY: subdirs $(CLEANDIRS)
.PHONY: all install clean
