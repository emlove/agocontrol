export CC = gcc
export CXX = g++
export LD = g++ 
export LDFLAGS = -L../../shared
export CFLAGS = -Wall -Wno-format -g -DDEBUG -O2 -pipe
export INSTALL = install
export INSTALL_DIR = $(INSTALL) -p -d -o root -g root  -m  755
export INSTALL_PROGRAM = $(INSTALL) -p    -o root -g root  -m  755
export INSTALL_FILE    = $(INSTALL) -p    -o root -g root  -m  644

export INCLUDES = -I../../shared

export BINDIR = /opt/agocontrol/bin
export ETCDIR = /etc
export LIBDIR = /usr/lib
export CONFDIR = $(ETCDIR)/opt/agocontrol
export INCDIR = /usr/include/agocontrol
export DATADIR = /var/opt/agocontrol
export LOCALSTATEDIR = /var/opt/agocontrol
export HTMLDIR = /opt/agocontrol/html

ifdef DEB_BUILD_OPTIONS
export BUILDEXTRA=yes
endif

ifneq (,$(filter parallel=%,$(DEB_BUILD_OPTIONS)))
NUMJOBS = $(patsubst parallel=%,%,$(filter parallel=%,$(DEB_BUILD_OPTIONS)))
MAKEFLAGS += -j$(NUMJOBS)
else
MAKEFLAGS += -j4
endif
export MAKEFLAGS

DIRS = shared core devices conf

BUILDDIRS = $(DIRS:%=build-%)
INSTALLDIRS = $(DIRS:%=install-%)
CLEANDIRS = $(DIRS:%=clean-%)

all: $(BUILDDIRS)
$(DIRS): $(BUILDDIRS)
$(BUILDDIRS):
	$(MAKE) -C $(@:build-%=%)

build-core: build-shared
build-devices: build-shared

clean: $(CLEANDIRS)
$(CLEANDIRS): 
	$(MAKE) -C $(@:clean-%=%) clean

install: $(INSTALLDIRS)
	@echo Installing
	install -d $(DESTDIR)$(ETCDIR)
	install -d $(DESTDIR)$(BINDIR)
	install -d $(DESTDIR)$(INCDIR)
	install -d $(DESTDIR)$(LIBDIR)
	install -d $(DESTDIR)$(LOCALSTATEDIR)
	install -d $(DESTDIR)$(DATADIR)
	install -d $(DESTDIR)/var/crash
	install data/inventory.sql $(DESTDIR)$(DATADIR)
	install data/datalogger.sql $(DESTDIR)$(DATADIR)
	install gateways/agomeloware.py $(DESTDIR)$(BINDIR)
	install scripts/agososreport.sh $(DESTDIR)$(BINDIR)
	install scripts/convert-zwave-uuid.py $(DESTDIR)$(BINDIR)
	install scripts/convert-scenario.py $(DESTDIR)$(BINDIR)
	install scripts/convert-event.py $(DESTDIR)$(BINDIR)
	install scripts/convert-config.py $(DESTDIR)$(BINDIR)

$(INSTALLDIRS):
	$(MAKE) -C $(@:install-%=%) install

