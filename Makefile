LD     := g++

all: common messagesend resolver agotimer agozwave agochromoflex agoknx agorpc

common:
	$(MAKE) -C shared

messagesend: 
	$(MAKE) -C core/messagesend

resolver:
	$(MAKE) -C core/resolver

agotimer:
	$(MAKE) -C core/agotimer

agozwave:
	$(MAKE) -C devices/agozwave

agorpc:
	$(MAKE) -C core/rpc

agochromoflex:
	$(MAKE) -C devices/chromoflex

agoknx:
	$(MAKE) -C devices/agoknx

agodmx:
	$(MAKE) -C devices/agodmx

clean:
	$(MAKE) -C shared clean
	$(MAKE) -C devices/chromoflex clean
	$(MAKE) -C devices/agozwave clean
	$(MAKE) -C devices/agoknx clean
	$(MAKE) -C core/agotimer clean
	$(MAKE) -C core/resolver clean
	$(MAKE) -C core/messagesend clean
	$(MAKE) -C devices/agodmx clean

install:
	@echo Installing
	install -d $(DESTDIR)/etc/opt/agocontrol
	install -d $(DESTDIR)/etc/opt/agocontrol/owfs
	install -d $(DESTDIR)/etc/opt/agocontrol/ozw
	install -d $(DESTDIR)/etc/opt/agocontrol/apc
	install -d $(DESTDIR)/etc/opt/agocontrol/jointspace
	install -d $(DESTDIR)/opt/agocontrol/bin
	install -d $(DESTDIR)/var/opt/agocontrol
	install -d $(DESTDIR)/usr/include/agocontrol
	install -d $(DESTDIR)/usr/lib
	install -d $(DESTDIR)/lib/systemd/system
	install conf/config.ini.tpl $(DESTDIR)/etc/opt/agocontrol
	install conf/schema.yaml $(DESTDIR)/etc/opt/agocontrol
	install conf/*.service $(DESTDIR)/lib/systemd/system
	install data/inventory.sql $(DESTDIR)/etc/opt/agocontrol
	install data/datalogger.sql $(DESTDIR)/etc/opt/agocontrol
	install core/agoresolver.py $(DESTDIR)/opt/agocontrol/bin
	install core/agodrain.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoscenario.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoevent.py $(DESTDIR)/opt/agocontrol/bin
	install core/inventory.py $(DESTDIR)/opt/agocontrol/bin
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
	install devices/agozwave/agozwave $(DESTDIR)/opt/agocontrol/bin
	install devices/agoknx/agoknx $(DESTDIR)/opt/agocontrol/bin
	install devices/chromoflex/agochromoflex $(DESTDIR)/opt/agocontrol/bin
	install devices/agoapc/agoapc.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agojointspace/agojointspace.py $(DESTDIR)/opt/agocontrol/bin
	install gateways/agomeloware.py $(DESTDIR)/opt/agocontrol/bin
	install core/messagesend.py $(DESTDIR)/opt/agocontrol/bin
	install core/messagesend/messagesend $(DESTDIR)/opt/agocontrol/bin
	install core/rpc/agorpc $(DESTDIR)/opt/agocontrol/bin
	install core/resolver/agoresolver $(DESTDIR)/opt/agocontrol/bin
	install core/agotimer/agotimer $(DESTDIR)/opt/agocontrol/bin
	install shared/libagoclient.so.1 $(DESTDIR)/usr/lib
	install shared/agoclient.h $(DESTDIR)/usr/include/agocontrol
#	install devices/agodmx/agodmx $(DESTDIR)/opt/agocontrol/bin
