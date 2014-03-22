#!/usr/bin/env bash
TMPFILE=$(mktemp -u).xml.in
SOURCEFILE=$(realpath $1)
ln -s ${SOURCEFILE} ${TMPFILE}
intltool-merge -x html/po ${TMPFILE} $2

# Remove first line: <?xml version...
# sed -i is not POSIX, and behaves differently on BSD vs GNU
if [ `uname -s` == "FreeBSD" ]; then
	sed -i '' '1d' $2
else
	sed -i '1d' $2
fi

rm ${TMPFILE}
