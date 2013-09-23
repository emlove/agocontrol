all:
	./mergetranslations.sh

clean:
	echo clean
	find ./templates -name "*.html" | grep -v in.html | while read file ; do rm $$file ; done
