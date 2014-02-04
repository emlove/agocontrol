#!/usr/bin/env bash
TMPFILE=$(mktemp -u).xml.in
SOURCEFILE=$(realpath $1)
ln -s ${SOURCEFILE} ${TMPFILE}
intltool-merge -x html/po ${TMPFILE} $2
sed -i '1d' $2
rm ${TMPFILE}
