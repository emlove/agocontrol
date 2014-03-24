#/bin/bash

cd templates
for i in `find . -name \*in.html`; 
    do ln -s `basename "$i"` "${i%.*.*}.xml.in";
done
cd ..

cd plugins
for i in `find . -name \*in.html`; 
    do ln -s `basename "$i"` "${i%.*.*}.xml.in";
done
cd ..

cd po
intltool-update -p -x -g agocontrol
for i  in *.po;
    do msgmerge -U "$i" agocontrol.pot;
done
cd ..

for i in `find . -name \*xml.in`; 
    do rm "$i";
done
