#!/usr/bin/python

# copyright (c) 2013 Harald Klein <hari+ago@vt100.at>
#

import agoclient
import smtplib
import string

client = agoclient.AgoConnection("smtp")
smtpserver = agoclient.getConfigOption("smtp", "server", "mx.mail.com")
smtpport = agoclient.getConfigOption("smtp", "port", "25")
smtpfrom = agoclient.getConfigOption("smtp", "from", "agoman@agocontrol.com")

def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "sendmail" and "to" in content:
			print "sending email"
			subject = "mail from agoman"
			if "subject" in content:
				subject = content["subject"]
			body = "no text"
			if "body" in content:
				body = content["body"]
			body = string.join((
				"From: %s" % smtpfrom,
				"To: %s" % content["to"],
				"Subject: %s" % subject ,
				"",
				body
				), "\r\n")
			try:
				server = smtplib.SMTP(smtpserver, smtpport)
				server.sendmail(smtpfrom,[content["to"]], body)
				return 0
			except:
				print "error sending email, check your config"
				return -1

client.addHandler(messageHandler)

client.addDevice("smtp", "smtpgateway")

client.run()

