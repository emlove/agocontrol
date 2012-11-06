#!/usr/bin/python
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

stream = file('schema.yaml','r')
data = load(stream, Loader=Loader)

print data
