#/bin/bash
cd templates
for i in `find . -name \*in.html`; 
    do ln -s `basename "$i"` "${i%.*.*}.xml.in";
done
cd ..

for i in `find . -name \*in.html`; do 
    intltool-merge -x po "$i" "${i%.*.*}.html";
    sed -i '1d' "${i%.*.*}.html";
done

find . -name "*xml.in" -exec rm \{} \;
