LD     := g++

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

install:
	@echo Installing
	install -d $(DESTDIR)/etc/opt/agocontrol
	install -d $(DESTDIR)/etc/opt/agocontrol/uuidmap
	install -d $(DESTDIR)/etc/opt/agocontrol/owfs
	install -d $(DESTDIR)/etc/opt/agocontrol/ozw
	install -d $(DESTDIR)/etc/opt/agocontrol/apc
	install -d $(DESTDIR)/etc/opt/agocontrol/jointspace
	install -d $(DESTDIR)/opt/agocontrol/bin
	install -d $(DESTDIR)/var/opt/agocontrol
	install -d $(DESTDIR)/usr/include/agocontrol
	install -d $(DESTDIR)/usr/lib
	install -d $(DESTDIR)/lib/systemd/system
	install -d $(DESTDIR)/etc/sysctl.d
	install -d $(DESTDIR)/etc/security/limits.d
	install -d $(DESTDIR)/var/crash
	install conf/security-limits.conf $(DESTDIR)/etc/security/limits.d/agocontrol.conf
	install conf/sysctl.conf $(DESTDIR)/etc/sysctl.d/agocontrol.conf
	install conf/config.ini.tpl $(DESTDIR)/etc/opt/agocontrol
	install conf/schema.yaml $(DESTDIR)/etc/opt/agocontrol
	install conf/rpc_cert.pem $(DESTDIR)/etc/opt/agocontrol
	install conf/*.service $(DESTDIR)/lib/systemd/system
	install data/inventory.sql $(DESTDIR)/etc/opt/agocontrol
	install data/datalogger.sql $(DESTDIR)/etc/opt/agocontrol
	install core/agodrain.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoscenario.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoevent.py $(DESTDIR)/opt/agocontrol/bin
	install core/boolParser.py $(DESTDIR)/opt/agocontrol/bin
	install core/myavahi.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoctrl.sh $(DESTDIR)/opt/agocontrol/bin
	install core/agodatalogger.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agologger.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agoowfs.py $(DESTDIR)/opt/agocontrol/bin
	install devices/enigma2/agoenigma2.py $(DESTDIR)/opt/agocontrol/bin
	install devices/asterisk/agoasterisk.py $(DESTDIR)/opt/agocontrol/bin
	install devices/onkyo/core.py $(DESTDIR)/opt/agocontrol/bin
	install devices/onkyo/commands.py $(DESTDIR)/opt/agocontrol/bin
	install devices/onkyo/agoiscp.py $(DESTDIR)/opt/agocontrol/bin
	install devices/zwave/agozwave $(DESTDIR)/opt/agocontrol/bin
	install devices/agoknx/agoknx $(DESTDIR)/opt/agocontrol/bin
	install devices/firmata/agofirmata $(DESTDIR)/opt/agocontrol/bin
	install devices/rain8net/agorain8net $(DESTDIR)/opt/agocontrol/bin
	install devices/irtrans_ethernet/agoirtrans_ethernet $(DESTDIR)/opt/agocontrol/bin
	install devices/kwikwai/agokwikwai $(DESTDIR)/opt/agocontrol/bin
	install devices/blinkm/agoblinkm $(DESTDIR)/opt/agocontrol/bin
	install devices/i2c/agoi2c $(DESTDIR)/opt/agocontrol/bin
#	install devices/onvif/agoonvif $(DESTDIR)/opt/agocontrol/bin
	install devices/mediaproxy/agomediaproxy $(DESTDIR)/opt/agocontrol/bin
	install devices/chromoflex/agochromoflex $(DESTDIR)/opt/agocontrol/bin
	install devices/agoapc/agoapc.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agojointspace/agojointspace.py $(DESTDIR)/opt/agocontrol/bin
	install gateways/agomeloware.py $(DESTDIR)/opt/agocontrol/bin
	install core/messagesend.py $(DESTDIR)/opt/agocontrol/bin
	install core/messagesend/messagesend $(DESTDIR)/opt/agocontrol/bin
	install core/rpc/agorpc $(DESTDIR)/opt/agocontrol/bin
	install core/resolver/agoresolver $(DESTDIR)/opt/agocontrol/bin
	install core/manager/agoman $(DESTDIR)/opt/agocontrol/bin
	install core/agotimer/agotimer $(DESTDIR)/opt/agocontrol/bin
	install shared/libagoclient.so.1 $(DESTDIR)/usr/lib
	install shared/agoclient.h $(DESTDIR)/usr/include/agocontrol
	install shared/agoclient.py $(DESTDIR)/opt/agocontrol/bin
#	install devices/agodmx/agodmx $(DESTDIR)/opt/agocontrol/bin
	install scripts/agososreport.sh $(DESTDIR)/opt/agocontrol/bin
	install scripts/convert-zwave-uuid.py $(DESTDIR)/opt/agocontrol/bin
	install devices/raspiGPIO/raspiGPIO.py $(DESTDIR)/opt/agocontrol/bin
	install devices/raspi1wGPIO/raspi1wGPIO.py $(DESTDIR)/opt/agocontrol/bin
	install devices/raspiMCP3xxxGPIO/raspiMCP3xxxGPIO.py $(DESTDIR)/opt/agocontrol/bin
	install devices/gc100/agogc100.py $(DESTDIR)/opt/agocontrol/bin
