#!/usr/bin/python
import sys
sys.path.append('/opt/agocontrol/bin')
import agoclient

import cgi
import cgitb

import subprocess
import urllib2

from nss.error import NSPRError
import nss.io as io
import nss.nss as nss
import nss.ssl as ssl

cgitb.enable()

certdir = '/etc/opt/agocontrol/cloud'

def password_callback(slot, retry, password):
	with open (certdir + "pwfile", "r") as pwfile:
		data = pwfile.read()
		return data

def read_cert(certdir, name):
	try:
		nss.nss_init(certdir)
		certdb = nss.get_default_certdb()
		nss.set_password_callback(password_callback)
		cert = nss.find_cert_from_nickname(uuid)
		print "<H1>Certificate details</H1>"
		print "Serial: %#x<br>" % cert.serial_number
		print "Valid from: %s<br>" % cert.valid_not_before_str
		print "Valid until: %s<br>" % cert.valid_not_after_str
		
	except NSPRError:
		print "NSPR Error"
		return -1
	except:
		print "can't open"
		return -1
	return 0

def getP12(SYSTEM_UUID, username, password, pin):
	url = "http://cloud.agocontrol.com/agoka/?uuid=%s&username=%s&password=%s" % (SYSTEM_UUID, username, password)
	file_name = "/tmp/%s.p12" % SYSTEM_UUID
	u = urllib2.urlopen(url)
	buffer = u.read()
	if 'Incorrect username or password.' in buffer:
		result = "Activation failed, please verify that username and password are correct. Please also check that you have a valid subscription for the ago cloud service"
		print result
	else:
		f = open(file_name, 'wb')
		f.write(buffer)
		f.close()
		ret = subprocess.call(["/opt/agocontrol/bin/agocloud-import.sh", file_name, pin])


print "Content-Type: text/html"
print
print "<HEAD></HEAD><BODY>"

form = cgi.FieldStorage()
uuid = agoclient.getConfigOption("system", "uuid", "")

if "action" not in form:
	print "<H1>Certificate information</H1>"
	read_cert(certdir, uuid)
else:	
	if "username" not in form or "password" not in form:
		print "<H1>Error</H1>"
		print "please provide uuid, username and password"

	username=form.getfirst("username")
	password=form.getfirst("password")
	pin=form.getfirst("pin")
	getP12(uuid, username, password, pin)
	if (read_cert(certdir, uuid) == 0):
		print "<H1>Success</H1><P>Activation Successful"
	else:
		print "<H1>Error</H1>Cannot import certificate. Please check your PIN code."


print "</BODY></HTML>"
