#!/bin/bash
dch -v ${1} "new package"
dch -r
echo "#define AGOCONTROL_VERSION \"${1}\"" > version.h
