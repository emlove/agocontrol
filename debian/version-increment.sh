#!/bin/bash
NUMCOMMIT=$(git rev-list --count HEAD)
GITSHORT=$(git rev-parse --short HEAD)
dch -v 1.0-${NUMCOMMIT}-${GITSHORT} "new package from ${1}"
dch -r "unstable"
VERSION=$(dpkg-parsechangelog  | grep ^Version | sed 's/^Version: //g')
echo "#define AGOCONTROL_VERSION \"${VERSION}\"" > version.h
