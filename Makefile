export uname_S := $(shell sh -c 'uname -s 2>/dev/null || echo not')

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

export BINDIR = $(DESTDIR)/opt/agocontrol/bin
export ETCDIR = $(DESTDIR)/etc
export LIBDIR = $(DESTDIR)/usr/lib
export CONFDIR = $(ETCDIR)/opt/agocontrol
export INCDIR = $(DESTDIR)/usr/include/agocontrol

ifeq ($(uname_S),FreeBSD)
LDFLAGS+=$(shell pkg-config uuid --libs)
CFLAGS+=$(shell pkg-config uuid --cflags)
endif

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

DIRS = shared core devices

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
	install -d $(ETCDIR)
	install -d $(BINDIR)
	install -d $(INCDIR)
	install -d $(LIBDIR)
	install -d $(DESTDIR)/var/opt/agocontrol
	install -d $(CONFDIR)/db
	install -d $(CONFDIR)/conf.d
	install -d $(CONFDIR)/old
	install -d $(CONFDIR)/rpc
	install -d $(CONFDIR)/uuidmap
	install -d $(CONFDIR)/maps
	install -d $(DESTDIR)/lib/systemd/system
	install -d $(ETCDIR)/sysctl.d
	install -d $(ETCDIR)/security/limits.d
	install -d $(DESTDIR)/var/crash
	install conf/security-limits.conf $(ETCDIR)/security/limits.d/agocontrol.conf
	install conf/sysctl.conf $(ETCDIR)/sysctl.d/agocontrol.conf
	install conf/conf.d/*.conf $(CONFDIR)/conf.d
	install conf/schema.yaml $(CONFDIR)
	install conf/rpc_cert.pem $(CONFDIR)/rpc
	install conf/systemd/*.service $(DESTDIR)/lib/systemd/system
	install data/inventory.sql $(DESTDIR)/var/opt/agocontrol
	install data/datalogger.sql $(DESTDIR)/var/opt/agocontrol
	install gateways/agomeloware.py $(BINDIR)
	install scripts/agososreport.sh $(BINDIR)
	install scripts/convert-zwave-uuid.py $(BINDIR)
	install scripts/convert-scenario.py $(BINDIR)
	install scripts/convert-event.py $(BINDIR)
	install scripts/convert-config.py $(BINDIR)

$(INSTALLDIRS):
	$(MAKE) -C $(@:install-%=%) install

