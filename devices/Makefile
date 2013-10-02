DIRS = agoEnOcean blinkm chromoflex firmata i2c irtrans_ethernet kwikwai mediaproxy rain8net zwave 1wire syslog enigma2 asterisk agoapc agojointspace raspiGPIO raspi1wGPIO raspiMCP3xxxGPIO gc100 onkyo x10 webcam

ifdef BUILDEXTRA
DIRS += agodmx knx 
endif

BUILDDIRS = $(DIRS:%=build-%)
INSTALLDIRS = $(DIRS:%=install-%)
CLEANDIRS = $(DIRS:%=clean-%)

all: $(BUILDDIRS)
$(DIRS): $(BUILDDIRS)
$(BUILDDIRS):
	$(MAKE) -C $(@:build-%=%)

install: $(INSTALLDIRS) all
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
