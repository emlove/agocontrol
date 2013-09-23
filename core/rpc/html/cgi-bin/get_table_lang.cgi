#!/usr/bin/python
import cgi
import os.path

print "Content-Type: text/plain\n\n"

form = cgi.FieldStorage()

filename = "../datatables_lang/%s.txt" % form.getfirst("lang")
if not os.path.isfile(filename):
    filename = "../datatables_lang/en.txt"

f = open(filename)
for line in f:
    print line.strip()
f.close()
