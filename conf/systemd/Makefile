# Generate a list of all .service files that need to be created
FILES = $(patsubst %.service.in, %.service, $(wildcard *.service.in))

%.service : %.service.in
	sed -e 's|@BINDIR|$(BINDIR)|g' $< > $@

all: $(FILES)

install:
	$(INSTALL_DIR) $(DESTDIR)/lib/systemd/system
	$(INSTALL_FILE) *.service $(DESTDIR)/lib/systemd/system

clean:
	-rm *.service
