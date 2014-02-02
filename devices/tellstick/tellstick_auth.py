#!/usr/bin/python

import sys, getopt, httplib, urllib, json, os
import logging, syslog
import oauth.oauth as oauth
from configobj import ConfigObj, ConfigObjError

def info (text):
    logging.info (text)
    syslog.syslog(syslog.LOG_INFO, text)
    if debug:
        print "INF " + text + "\n"
def debug (text):
    logging.debug (text)
    syslog.syslog(syslog.LOG_DEBUG, text)
    if debug:
        print "DBG " + text + "\n"
def error (text):
    logging.error(text)
    syslog.syslog(syslog.LOG_ERR, text)
    if debug:
        print "ERR " + text + "\n"
def warning(text):
    logging.warning (text)
    syslog.syslog(syslog.LOG_WARNING, text)
    if debug:
        print "WRN " + text + "\n"

class LogErr:
        def write(self, data):
                syslog.syslog(syslog.LOG_ERR, data)

syslog.openlog(sys.argv[0], syslog.LOG_PID, syslog.LOG_DAEMON)

logging.basicConfig(filename='/var/log/tellstick.log', format='%(asctime)s %(levelname)s:%(message)s', level=logging.INFO) #level=logging.DEBUG
#logging.setLevel( logging.INFO )


def doRequest(method, params):
	global config
	consumer = oauth.OAuthConsumer(PUBLIC_KEY, PRIVATE_KEY)
	token = oauth.OAuthToken(config['telldus']['token'], config['telldus']['tokenSecret'])

	oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='GET', http_url="http://api.telldus.com/json/" + method, parameters=params)
	oauth_request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), consumer, token)
	headers = oauth_request.to_header()
	headers['Content-Type'] = 'application/x-www-form-urlencoded'

	conn = httplib.HTTPConnection("api.telldus.com:80")
	conn.request('GET', "/json/" + method + "?" + urllib.urlencode(params, True).replace('+', '%20'), headers=headers)

	response = conn.getresponse()
	return json.load(response)

def requestToken():
	global config
	consumer = oauth.OAuthConsumer(PUBLIC_KEY, PRIVATE_KEY)
	request = oauth.OAuthRequest.from_consumer_and_token(consumer, http_url='http://api.telldus.com/oauth/requestToken')
	request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), consumer, None)
	conn = httplib.HTTPConnection('api.telldus.com:80')
	conn.request(request.http_method, '/oauth/requestToken', headers=request.to_header())

	resp = conn.getresponse().read()
	token = oauth.OAuthToken.from_string(resp)
	print 'Open the following url in your webbrowser:\nhttp://api.telldus.com/oauth/authorize?oauth_token=%s\n' % token.key
	print 'After logging in and accepting to use this application run:\n%s --authenticate' % (sys.argv[0])
	config['telldus']['requestToken'] = str(token.key)
	config['telldus']['requestTokenSecret'] = str(token.secret)
	saveConfig()

def getAccessToken():
	global config
	consumer = oauth.OAuthConsumer(PUBLIC_KEY, PRIVATE_KEY)
	token = oauth.OAuthToken(config['telldus']['requestToken'], config['telldus']['requestTokenSecret'])
	request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=token, http_method='GET', http_url='http://api.telldus.com/oauth/accessToken')
	request.sign_request(oauth.OAuthSignatureMethod_HMAC_SHA1(), consumer, token)
	conn = httplib.HTTPConnection('api.telldus.com:80')
	conn.request(request.http_method, request.to_url(), headers=request.to_header())

	resp = conn.getresponse()
	if resp.status != 200:
		print 'Error retreiving access token, the server replied:\n%s' % resp.read()
		return
	token = oauth.OAuthToken.from_string(resp.read())
	config['telldus']['requestToken'] = None
	config['telldus']['requestTokenSecret'] = None
	config['telldus']['token'] = str(token.key)
	config['telldus']['tokenSecret'] = str(token.secret)
	print 'Authentication successful, you can now use your Tellstick Net with aGo control'
	saveConfig()

def authenticate():
    try:
        x = config["telldus"]["first"]
        if x == "True":
            getAccessToken()
            return
    except KeyError:
        pass
    requestToken()

def saveConfig():
	global config
	config.write()

def main(argv):
    global config
    try:
        x = config["telldus"]
    except KeyError:
    	config['telldus'] = {"first": "True"}
    	saveConfig()

    if ('token' not in config or config['telldus']['token'] == ''):
        info ("call authenticate")
        authenticate()
        return

	for opt, arg in opts:
		if opt in ("-h", "--help"):
			pass

if __name__ == "__main__":
    debug = True
    config = ConfigObj("/etc/opt/agocontrol/conf.d/tellstick.conf")

    try:
        PUBLIC_KEY = config['keys']['PUBLIC_KEY']
    except KeyError:
        error ("PUBLIC_KEY missing in config file /etc/opt/agocontrol/conf.d/tellstick.conf Cannot continue.")
        quit()

    try:
        PRIVATE_KEY = config['keys']['PRIVATE_KEY']
    except KeyError:
        error ("PRIVATE_KEY missing in config file /etc/opt/agocontrol/conf.d/tellstick.conf Cannot continue.")
        quit()

    main(sys.argv[1:])
