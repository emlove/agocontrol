#
# copyright (c) 2013 Harald Klein <hari+ago@vt100.at>
#

import agoclient
import smtplib

client = agoclient.AgoConnection("smtp")
smtpserver = agoclient.getConfigOption("smtp", "server", "mx.mail.com")
smtpport = agoclient.getConfigOption("smtp", "port", "25")
smtpfrom = agoclient.getConfigOption("smtp", "from", "agoman@agocontrol.com")


def messageHandler(internalid, content):
	if "command" in content:
		if content["command"] == "sendmail" and "to" in content and "subject" in content:
			server = smtplib.SMTP(smtpserver, smtpport)
			body = string.join((
				"From: %s" % smtpfrom,
				"To: %s" % content["to"],
				"Subject: %s" % content["subject"] ,
				"",
				content["body"]
				), "\r\n")
			server.sendmail(smtpfrom,[content["to"]], body)

client.addHandler(messageHandler)

client.addDevice("smtp", "smtpgateway")

client.run()

