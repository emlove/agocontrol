LD     := g++

all: messagesend  agotimer agozwave agochromoflex agoknx

messagesend: 
	$(MAKE) -C core/messagesend

agotimer:
	$(MAKE) -C core/agotimer

agozwave:
	$(MAKE) -C devices/agozwave

agochromoflex:
	$(MAKE) -C devices/chromoflex

agoknx:
	$(MAKE) -C devices/agoknx

clean:
	$(MAKE) -C devices/chromoflex clean
	$(MAKE) -C devices/agozwave clean
	$(MAKE) -C devices/agoknx clean
	$(MAKE) -C core/agotimer clean
	$(MAKE) -C core/messagesend clean

install:
	@echo Installing
	install -d $(DESTDIR)/etc/opt/agocontrol
	install -d $(DESTDIR)/etc/opt/agocontrol/owfs
	install -d $(DESTDIR)/etc/opt/agocontrol/ozw
	install -d $(DESTDIR)/opt/agocontrol/bin
	install -d $(DESTDIR)/lib/systemd/system
	install conf/config.ini.tpl $(DESTDIR)/etc/opt/agocontrol
	install conf/schema.yaml $(DESTDIR)/etc/opt/agocontrol
	install conf/*.service $(DESTDIR)/lib/systemd/system
	install data/inventory.sql $(DESTDIR)/etc/opt/agocontrol
	install core/agoresolver.py $(DESTDIR)/opt/agocontrol/bin
	install core/agodrain.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoscenario.py $(DESTDIR)/opt/agocontrol/bin
	install core/agoevent.py $(DESTDIR)/opt/agocontrol/bin
	install core/inventory.py $(DESTDIR)/opt/agocontrol/bin
	install core/boolParser.py $(DESTDIR)/opt/agocontrol/bin
	install core/myavahi.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agologger.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agoowfs.py $(DESTDIR)/opt/agocontrol/bin
	install devices/onkyo/core.py $(DESTDIR)/opt/agocontrol/bin
	install devices/onkyo/commands.py $(DESTDIR)/opt/agocontrol/bin
	install devices/onkyo/agoiscp.py $(DESTDIR)/opt/agocontrol/bin
	install devices/agozwave/agozwave $(DESTDIR)/opt/agocontrol/bin
	install devices/agoknx/agoknx $(DESTDIR)/opt/agocontrol/bin
	install devices/chromoflex/agochromoflex $(DESTDIR)/opt/agocontrol/bin
	install gateways/agomeloware.py $(DESTDIR)/opt/agocontrol/bin
	install core/messagesend.py $(DESTDIR)/opt/agocontrol/bin
	install core/messagesend/messagesend $(DESTDIR)/opt/agocontrol/bin
	install core/agotimer/agotimer $(DESTDIR)/opt/agocontrol/bin
