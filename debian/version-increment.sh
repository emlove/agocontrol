#!/bin/bash
NUMCOMMIT=$(git rev-list --count HEAD)
dch -v ${NUMCOMMIT} "new package from ${1}"
dch -r "unstable"
VERSION=$(dpkg-parsechangelog  | grep ^Version | sed 's/^Version: //g')
echo "#define AGOCONTROL_VERSION \"${VERSION}-${NUMCOMMIT}\"" > version.h
