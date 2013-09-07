#!/bin/bash
dch -v ${1} "new package"
dch -r "unstable"
echo "#define AGOCONTROL_VERSION \"${1}\"" > version.h
