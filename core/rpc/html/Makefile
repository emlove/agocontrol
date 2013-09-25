MAKEFLAGS = -j1

all: mergetranslation

mergetranslation:
	./mergetranslations.sh

install:

clean:
	find ./templates -name "*.html" | grep -v in.html | while read file ; do rm -v $$file ; done
