#/bin/bash

cd templates
for i in `find . -name \*in.html`; 
    do ln -s `basename "$i"` "${i%.*.*}.xml.in";
done
cd ..

cd po
intltool-update -p -x -g agocontrol
cd ..

for i in `find . -name \*xml.in`; 
    do rm "$i";
done
