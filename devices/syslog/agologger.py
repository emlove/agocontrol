#! /usr/bin/env python

import sys
import syslog
import time
import agoclient

# route stderr to syslog
class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)
sys.stderr = LogErr()

syslog.syslog(syslog.LOG_NOTICE, "agologger.py startup")

client = agoclient.AgoConnection("logger")

def eventHandler(subject, content):
	syslog.syslog(syslog.LOG_NOTICE, "%s - %s" % (subject,content))

client.addEventHandler(eventHandler)

client.run()

