# Generate a list of all .conf files that need to be created
FILES = $(patsubst %.conf.in, %.conf, $(wildcard *.conf.in))

%.conf: %.conf.in
	sed -e 's|@CONFDIR@|$(CONFDIR)|g' \
		-e 's|@HTMLDIR@|$(HTMLDIR)|g' $< > $@

all: $(FILES)

install:
	install -d $(DESTDIR)$(CONFDIR)/conf.d
	install *.conf $(DESTDIR)$(CONFDIR)/conf.d

clean:
	-rm $(FILES)
