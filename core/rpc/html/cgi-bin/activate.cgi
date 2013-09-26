#!/usr/bin/python
import cgi
import cgitb

import subprocess

import urllib2


cgitb.enable()

print "Content-Type: text/html"
print
print "<HEAD></HEAD><BODY>"

def getP12(SYSTEM_UUID, username, password, pin):
	url = "http://cloud.agocontrol.com/agoka/?uuid=%s&username=%s&password=%s" % (SYSTEM_UUID, username, password)
	file_name = "/tmp/%s.p12" % SYSTEM_UUID
	u = urllib2.urlopen(url)
	buffer = u.read()
	if 'Incorrect username or password.' in buffer:
		result = "Activation failed, please verify that username and password are correct. Please also check that the installation uuid is active in the ago cloud service"
	else:
		f = open(file_name, 'wb')
		f.write(buffer)
		f.close()
		ret = subprocess.call(["/opt/agocontrol/bin/agocloud-import.sh", file_name, pin])
		if ret == 0:
			result = "Activation certificate was installed successfully"
		else:
			result = "Error, could not import certificate, check pin"
	print result



form = cgi.FieldStorage()
if "username" not in form or "password" not in form or "uuid" not in form:
	print "<H1>Error</H1>"
	print "please provide uuid, username and password"

uuid=form.getfirst("uuid")
username=form.getfirst("username")
password=form.getfirst("password")
pin=form.getfirst("pin")
# print "<p>username:", form["username"].value
# print "<p>password:", form["password"].value
# print "<p>uuid:", form["uuid"].value

getP12(uuid, username, password, pin)


