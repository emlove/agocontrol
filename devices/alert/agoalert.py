#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IPX800 relay board client
# http://gce-electronics.com
# copyright (c) 2013 tang
 
import sys
import agoclient
import threading
import time
import logging
from Queue import Queue
#gtalk libs
import xmpp
#twitter libs
import tweepy
#mail libs
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
#sms libs
import urllib
import urllib2
#pushover
import httplib
import json
#pushbullet
from pushbullet import PushBullet
#notifymyandroid
from xml.dom import minidom

client = None
twitter = None
mail = None
sms = None
gtalk = None
hangout = None
push = None

STATE_GTALK_CONFIGURED = '11'
STATE_GTALK_NOT_CONFIGURED = '10'
STATE_MAIL_CONFIGURED = '21'
STATE_MAIL_NOT_CONFIGURED = '20'
STATE_SMS_CONFIGURED = '31'
STATE_SMS_NOT_CONFIGURED = '30'
STATE_TWITTER_CONFIGURED = '41'
STATE_TWITTER_NOT_CONFIGURED = '40'
STATE_PUSH_CONFIGURED = '51'
STATE_PUSH_NOT_CONFIGURED = '50'
STATE_GROWL_CONFIGURED = '61'
STATE_GROWL_NOT_CONFIGURED = '60'

#logging.basicConfig(filename='agoalert.log', level=logging.INFO, format="%(asctime)s %(levelname)s : %(message)s")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s : %(message)s")

#=================================
#classes
#=================================
class AgoAlert(threading.Thread):
    """base class for agoalert message"""
    def __init__(self):
        threading.Thread.__init__(self)
        self.__running = True
        self.__queue = Queue()
        self.name = ''

    def __del__(self):
        self.stop()

    def stop(self):
        self.__running = False

    def _addMessage(self, message):
        """Queue specified message"""
        self.__queue.put(message)

    def getConfig(self):
        """return if module is configured or not"""
        raise NotImplementedError('configured method must be implemented')

    def _sendMessage(self, message):
        """send message"""
        raise NotImplementedError('_sendMessage method must be implemented')

    def run(self):
        """main process"""
        while self.__running:
            if not self.__queue.empty():
                #message to send
                message = self.__queue.get()
                logging.info('send message: %s' % str(message))
                try:
                    self._sendMessage(message)
                except Exception as e:
                    logging.exception('Unable to send message:')
            #pause
            time.sleep(0.25)

class Dummy(AgoAlert):
    """Do nothing"""
    def __init__(self):
        """Contructor"""
        AgoAlert.__init__(self)

    def getConfig(self):
        return {'configured':0}

    def _sendMessage(self, message):
        pass

class SMS12voip(AgoAlert):
    """Class to send text message (SMS) using 12voip.com provider"""
    def __init__(self, username, password):
        """Contructor"""
        AgoAlert.__init__(self)
        self.username = username
        self.password = password
        self.name = '12voip'
        if username and len(username)>0 and password and len(password)>0:
            self.__configured = True
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_SMS_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_SMS_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        return {'configured':configured, 'username':self.username, 'password':self.password}

    def setConfig(self, username, password):
        """Set config
           @param username: 12voip username
           @param password: 12voip password"""
        if not username or len(username)==0 or not password or len(password)==0:
            logging.error('SMS12voip: invalid parameters')
            return False
        if not agoclient.setConfigOption('12voip', 'username', username, 'alert') or not agoclient.setConfigOption('12voip', 'password', password, 'alert'):
            logging.error('SMS12voip: unable to save config')
            return False
        self.username = username
        self.password = password
        self.__configured = True
        client.emitEvent('alertcontroller', "event.device.statechanged", STATE_SMS_NOT_CONFIGURED, "")
        return True

    def addSMS(self, to, text):
        """Add SMS"""
        if self.__configured:
            #check parameters
            if not to or not text or len(to)==0 or len(text)==0:
                logging.error('SMS12voip: Unable to add SMS because all parameters are mandatory')
                return False
            if not to.startswith('+') and to!=self.username:
                logging.error('SMS12voip: Unable to add SMS because "to" number must be international number')
                return False
            if len(text)>160:
                logging.warning('SMS12voip: SMS is too long, message will be truncated')
                text = text[:159]
            #queue sms
            self._addMessage({'to':to, 'text':text})
            return True
        else:
            logging.error('SMS12voip: unable to add SMS because not configured')
            return False

    def _sendMessage(self, message):
        """url format:
           https://www.12voip.com/myaccount/sendsms.php?username=xxxxxxxxxx&password=xxxxxxxxxx&from=xxxxxxxxxx&to=xxxxxxxxxx&text=xxxxxxxxxx""" 
        params = {'username':self.username, 'password':self.password, 'from':self.username, 'to':message['to'], 'text':message['text']}
        url = 'https://www.12voip.com/myaccount/sendsms.php?'
        url += urllib.urlencode(params)
        req = urllib2.urlopen(url)
        lines = req.readlines()
        req.close()
        logging.debug(url)

class GTalk(AgoAlert):
    """Class for GTalk message sending"""
    def __init__(self, username, password):
        """constructor"""
        AgoAlert.__init__(self)
        self.username = username
        self.password = password
        self.name = 'gtalk'
        if username and len(username)>0 and password and len(password)>0:
            self.__configured = True
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_GTALK_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_GTALK_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        return {'configured':configured, 'username':self.username, 'password':self.password}

    def setConfig(self, username, password):
        """set gtalk config
           @param username: must be your google username (ending with @gmail.com)
           @param password: your password or 2-step verification token
           @info generate token here : https://www.google.com/settings/security""" 
        if not username or len(username)==0 or not password or len(password)==0:
            logging.error('GTalk: Unable to add SMS because all parameters are mandatory')
            return False
        if not agoclient.setConfigOption('gtalk', 'username', username, 'alert') or not agoclient.setConfigOption('gtalk', 'password', password, 'alert'):
            logging.error('GTalk: unable to save config')
            return False
        self.username = username
        self.password = password
        self.__configured = True
        client.emitEvent('alertcontroller', "event.device.statechanged", STATE_GTALK_CONFIGURED, "")
        return True

    def addMessage(self, to, message):
        """Add GTalk message"""
        if self.__configured:
            #check parameters
            if not to or len(to)==0 or not message or len(message)==0:
                logging.error('GTalk: Unable to add message because all parameters are mandatory')
                return False
            #queue message
            self._addMessage({'to':to, 'message':message})
            return True
        else:
            logging.error('GTalk: unable to add message because not configured')
            return False

    def _sendMessage(self, message):
       jid = xmpp.protocol.JID( self.username )
       connection = xmpp.Client('gmail.com', debug=[])
       #connection = xmpp.Client('gmail.com', debug=[]) #no debug
       connection.connect( ( 'talk.google.com', 5222 ) )
       connection.auth( jid.getNode( ), self.password, 'agocontrol' )
       connection.sendInitPresence()
       connection.send( xmpp.protocol.Message( message['to'], message['message'], typ='chat' ) )

class Twitter(AgoAlert):
    """Class for tweet sending"""
    def __init__(self, key, secret):
        """constructor"""
        AgoAlert.__init__(self)
        global client
        self.consumerKey = '8SwEenXApf9NNpufRk171g'
        self.consumerSecret = 'VoVGMLU63VThwRBiC1uwN3asR5fqblHBQyn8EZq2Q'
        self.name = 'twitter'
        self.__auth = None
        self.key = key
        self.secret = secret
        if key and len(key)>0 and secret and len(secret)>0:
            self.__configured = True
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_TWITTER_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_TWITTER_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        return {'configured':configured}

    def setAccessCode(self, code):
        """Set twitter access code to get user key and secret
           @param code: code provided by twitter """
        if code and len(code)>0:
            try:
                if not self.__auth:
                    self.__auth = tweepy.OAuthHandler(self.consumerKey, self.consumerSecret)
                    self.__auth.secure = True
                #get token
                token = self.__auth.get_access_token(code)
                #save token internally
                self.key = token.key
                self.secret = token.secret
                #save token in config file
                if agoclient.setConfigOption('twitter', 'key', self.key, 'alert') and agoclient.setConfigOption('twitter', 'secret', self.secret, 'alert'):
                    self.__configured = True
                    client.emitEvent('alertcontroller', "event.device.statechanged", STATE_TWITTER_CONFIGURED, "")
                    return {'error':0, 'msg':''}
                else:
                    return {'error':0, 'msg':'Unable to save Twitter token in config file.'}
            except Exception as e:
                logging.error('Twitter: config exception [%s]' % str(e))
                return {'error':1, 'msg':'Internal error'}
        else:
            logging.error('Twitter: code is mandatory')
            return {'error':1, 'msg':'Internal error'}

    def getAuthorizationUrl(self):
        """get twitter authorization url"""
        try:
            if not self.__auth:
                self.__auth = tweepy.OAuthHandler(self.consumerKey, self.consumerSecret)
                self.__auth.secure = True
            url = self.__auth.get_authorization_url()
            #logging.info('twitter url=%s' % url)
            return {'error':0, 'url':url}
        except Exception as e:
            logging.exception('Twitter: Unable to get Twitter authorization url [%s]' % str(e) ) 
            return {'error':1, 'url':''}

    def addTweet(self, tweet):
        """Add tweet"""
        if self.__configured:
            #check parameters
            if not tweet and len(tweet)==0:
                logging.error('Twitter: Unable to add tweet (all parameters are mandatory)')
                return False
            if len(tweet)>140:
                logging.warning('Twitter: Tweet is too long, message will be truncated')
                tweet = tweet[:139]
            #queue message
            self._addMessage({'tweet':tweet})
            return True
        else:
            logging.error('Twitter: unable to add tweet because not configured')
            return False

    def _sendMessage(self, message):
        #connect using OAuth auth (basic auth deprecated)
        auth = tweepy.OAuthHandler(self.consumerKey, self.consumerSecret)
        auth.secure = True
        logging.debug('key=%s secret=%s' % (self.key, self.secret))
        auth.set_access_token(self.key, self.secret)
        api = tweepy.API(auth)
        api.update_status(message['tweet'])

class Mail(AgoAlert):
    """Class for mail sending"""
    def __init__(self, smtp, sender, login, password, tls):
        """Constructor"""
        AgoAlert.__init__(self)
        global client
        self.smtp = smtp
        self.sender = sender
        self.login = login
        self.password = password
        self.tls = False
        if tls=='1':
            self.tls = True
        self.name = 'mail'
        if smtp and len(smtp)>0 and sender and len(sender)>0:
            self.__configured = True
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_MAIL_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_MAIL_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        tls = 0
        if self.tls:
            tls = 1
        return {'configured':configured, 'sender':self.sender, 'smtp':self.smtp, 'login':self.login, 'password':self.password, 'tls':tls}

    def setConfig(self, smtp, sender, login, password, tls):
        """set config
           @param smtp: smtp server address
           @param sender: mail sender""" 
        if not smtp or len(smtp)==0 or not sender or len(sender)==0:
            logging.error('Mail: all parameters are mandatory')
            return False
        if not agoclient.setConfigOption('mail', 'smtp', smtp, 'alert') or not agoclient.setConfigOption('mail', 'sender', sender, 'alert') or not agoclient.setConfigOption('mail', 'login', login, 'alert') or not agoclient.setConfigOption('mail', 'password', password, 'alert') or not agoclient.setConfigOption('mail', 'tls', tls, 'alert'):
            logging.error('Mail: unable to save config')
            return False
        self.smtp = smtp
        self.sender = sender
        self.login = login
        self.password = password
        self.tls = False
        if tls=='1':
            self.tls = True
        self.__configured = True
        client.emitEvent('alertcontroller', "event.device.statechanged", STATE_MAIL_CONFIGURED, "")
        return True

    def addMail(self, tos, subject, content):
        """Add mail
           @param subject: mail subject
           @param tos: send mail to list of tos
           @param content: mail content"""
        if self.__configured:
            #check params
            if not subject or not tos or not content or len(tos)==0 or len(content)==0:
                logging.error('Mail: Unable to add mail (all parameters are mandatory)')
                return False
            if not subject:
                subject = 'AgoControlAlert'
            #queue mail
            self._addMessage({'subject':subject, 'tos':tos, 'content':content})
            return True
        else:
            logging.error('Mail: unable to add mail because not configured')
            return False

    def _sendMessage(self, message):
        mails = smtplib.SMTP(self.smtp)
        if self.tls:
            mails.starttls()
        if len(self.login)>0:
            mails.login(self.login, self.password)
        mail = MIMEMultipart('alternative')
        mail['Subject'] = message['content']
        mail['From'] = self.sender
        mail['To'] = message['tos'][0]
        text = """%s""" % (message['content'])
        html  = "<html><head></head><body>%s</body>" % (message['content'])
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        mail.attach(part1)
        mail.attach(part2)
        mails.sendmail(self.sender, message['tos'], mail.as_string())
        mails.quit()

class Pushover(AgoAlert):
    """Class for push message sending for ios and android"""
    def __init__(self, userid):
        """Constructor"""
        """https://pushover.net/"""
        AgoAlert.__init__(self)
        global client
        self.name = 'pushover'
        self.token = 'as9S9uyXocZiW7G6KLRgLvSFkFnDZz'
        self.userid = userid
        self.pushTitle = 'Agocontrol'
        if userid and len(userid)>0:
            self.__configured = True
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        return {'configured':configured, 'userid':self.userid, 'provider':self.name}

    def setConfig(self, userid):
        """set config
           @param userid: pushover userid (available on https://pushover.net/dashboard)"""
        if not userid or len(userid)==0:
            logging.error('Pushover: all parameters are mandatory')
            return False
        if not agoclient.setConfigOption('push','provider','pushover','alert') or not agoclient.setConfigOption('pushover', 'userid', userid, 'alert'):
            logging.error('Pushover: unable to save config')
            return False
        self.userid = userid
        self.__configured = True
        client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_CONFIGURED, "")
        return True

    def addPush(self, message, priority='0'):
        """Add push
           @param message: push notification"""
        if self.__configured:
            #check params
            if not message or len(message)==0 or not priority or len(priority)==0:
                logging.error('Pushover: Unable to add push (all parameters are mandatory)')
                return False
            #queue push message
            self._addMessage({'message':message, 'priority':priority})
            return True
        else:
            logging.error('Pushover: unable to add message because not configured')
            return False

    def _sendMessage(self, message):
        conn = httplib.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.urlencode({
            'token': self.token,
            'user':self.userid,
            'message':message['message'],
            'priority':message['priority'],
            'title':self.pushTitle,
            'timestamp': int(time.time())
        }), { "Content-type": "application/x-www-form-urlencoded" })
        resp = conn.getresponse()
        #check response
        if resp:
            try:
                resp = json.dumps(resp.read())
                #TODO manage receipt https://pushover.net/api#receipt
                if resp['status']==0:
                    #error occured
                    logging.error('Pushover: %s' % (str(resp['errors'])))
                else:
                    logging.info('Pushover: message received by user')
            except:
                logging.exception('Pushover: Exception push message')

class Pushbullet(AgoAlert):
    """Class for push message sending for ios and android
       @info https://www.pushbullet.com """
    def __init__(self, apikey, devices):
        """Constructor"""
        AgoAlert.__init__(self)
        global client
        self.name = 'pushbullet'
        self.pushbullet = None
        self.apikey = apikey
        if len(devices)==0:
            self.devices = []
        else:
            self.devices = json.loads(devices)
        self.pbdevices = {}
        self.pushTitle = 'Agocontrol'
        if apikey and len(apikey)>0 and devices and len(devices)>0:
            self.__configured = True
            self.pushbullet = PushBullet(self.apikey)
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        return {'configured':configured, 'apikey':self.apikey, 'devices':self.devices, 'provider':self.name}

    def getPushbulletDevices(self, apikey=None):
        """request pushbullet to get its devices"""
        if not self.__configured and not apikey:
            logging.error('Pushbullet: unable to get devices. Not configured and no apikey specified')
            return {}
        
        if apikey:
            self.pushbullet = PushBullet(apikey)

        devices = []
        if self.pushbullet:
            devs = self.pushbullet.getDevices()
            logging.debug('pushbullet devs=%s' % str(devs))
            for dev in devs:
                name = '%s %s (%s)' % (dev['extras']['manufacturer'], dev['extras']['model'], dev['id'])
                self.pbdevices[name] = {'name':name, 'id':dev['id']}
                devices.append(name)
        else:
            logging.error('Pushbullet: unable to get devices because not configured')
        return devices

    def setConfig(self, apikey, devices):
        """set config
           @param apikey: pushbullet apikey (available on https://www.pushbullet.com/account)
           @param devices: array of devices (id) to send notifications """
        if not apikey or len(apikey)==0 or not devices or len(devices)==0:
            logging.error('Pushbullet: all parameters are mandatory')
            return False
        if not agoclient.setConfigOption('push', 'provider', 'pushbullet','alert') or not agoclient.setConfigOption('pushbullet', 'apikey', apikey, 'alert') or not agoclient.setConfigOption('pushbullet', 'devices', json.dumps(devices), 'alert'):
            logging.error('Pushbullet: unable to save config')
            return False
        self.apikey = apikey
        self.devices = devices
        self.pbdevices = {}
        self.pushbullet = PushBullet(self.apikey)
        self.__configured = True
        client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_CONFIGURED, "")
        return True

    def addPush(self, message, file=None):
        """Add push
           @param message: push notification
           @file: full file path to send"""
        if self.__configured:
            #check params
            if not message or len(message)==0:
                if not file or len(file)==0:
                    logging.error('Pushbullet: Unable to add push (at least one parameter is mandatory)')
                    return False
            elif not file or len(file)==0:
                if not message or len(message)==0:
                    logging.error('Pushbullet: Unable to add push (at least one parameter is mandatory)')
                    return False
            if message==None:
                message = ''
            if file==None:
                file = ''
            #queue push message
            self._addMessage({'message':message, 'file':file})
            return True
        else:
            logging.error('Pushover: unable to add message because not configured')
            return False

    def _sendMessage(self, message):
        #get devices from pushbullet if necessary
        if len(self.pbdevices)==0:
            self.getPushbulletDevices()

        #push message
        for device in self.devices:
            #get device id
            if self.pbdevices.has_key(device):
                if len(message['file'])==0:
                    #send a note
                    resp = self.pushbullet.pushNote(self.pbdevices[device]['id'], self.pushTitle, message['message'])
                    logging.info(resp)
                else:
                    #send a file
                    resp = self.pushbullet.pushFile(self.pbdevices[device]['id'], message['file'])
            else:
                logging.warning('Pushbullet: unable to push notification to device "%s" because not found' % (device))

class Notifymyandroid(AgoAlert):
    """Class push notifications using notifymyandroid"""
    def __init__(self, apikeys):
        """Constructor"""
        """http://www.notifymyandroid.com"""
        AgoAlert.__init__(self)
        global client
        self.name = 'notifymyandroid'
        if not apikeys or len(apikeys)==0:
            self.apikeys = []
        else:
            self.apikeys = json.loads(apikeys)
        self.pushTitle = 'Agocontrol'
        if apikeys and len(apikeys)>0:
            self.__configured = True
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_CONFIGURED, "")
        else:
            self.__configured = False
            client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_NOT_CONFIGURED, "")

    def getConfig(self):
        configured = 0
        if self.__configured:
            configured = 1
        return {'configured':configured, 'apikeys':self.apikeys, 'provider':self.name}

    def setConfig(self, apikeys):
        """set config
           @param apikey: notifymyandroid apikey (available on https://www.notifymyandroid.com/account.jsp)"""
        if not apikeys or len(apikeys)==0:
            logging.error('Notifymyandroid: all parameters are mandatory')
            return False
        if not agoclient.setConfigOption('push','provider','notifymyandroid','alert') or not agoclient.setConfigOption('notifymyandroid', 'apikeys', json.dumps(apikeys) , 'alert'):
            logging.error('Notifymyandroid: unable to save config')
            return False
        self.apikeys = apikeys
        self.__configured = True
        client.emitEvent('alertcontroller', "event.device.statechanged", STATE_PUSH_CONFIGURED, "")
        return True

    def addPush(self, message, priority='0'):
        """Add push
           @param message: push notification"""
        if self.__configured:
            #check params
            if not message or len(message)==0 or not priority or len(priority)==0:
                logging.error('Notifymyandroid: Unable to add push (all parameters are mandatory)')
                return False
            #queue push message
            self._addMessage({'message':message, 'priority':str(priority)})
            return True
        else:
            logging.error('Notifymyandroid: unable to add message because not configured')
            return False

    def _sendMessage(self, message):
        for apikey in self.apikeys:
            conn = httplib.HTTPSConnection("www.notifymyandroid.com:443")
            conn.request("POST", "/publicapi/notify",
            urllib.urlencode({
                'apikey': apikey,
                'application':self.pushTitle,
                'event':'Agocontrol alert',
                'description':message['message'],
                'priority':message['priority'],
                'content-type': 'text/html'
            }), { "Content-type": "application/x-www-form-urlencoded" })
            resp = conn.getresponse()
            #check response
            if resp:
                try:
                    xml = resp.read()
                    dom = minidom.parseString(xml)
                    result = dom.firstChild.childNodes[0].tagName
                    code = dom.firstChild.childNodes[0].getAttribute('code')
                    if result=='success':
                        logging.info('Notifymyandoid: message pushed successfully')
                    elif result=='error':
                        logging.error('Notifymyandroid: received error code "%s"' % code)
                except:
                    logging.exception('Notifymyandroid: Exception push message')


#=================================
#utils
#=================================
def quit(msg):
    """Exit application"""
    global sms, hangout, mail, twitter, gtalk, push
    global client
    if client:
        del client
        client = None
    if sms:
        sms.stop()
        del sms
        sms = None
    if twitter:
        twitter.stop()
        del twitter
        twitter = None
    if hangout:
        hangout.stop()
        del hangout
        hangout = None
    if gtalk:
        gtalk.stop()
        del gtalk
        gtalk = None
    if mail:
        mail.stop()
        del mail
        mail = None
    if push:
        push.stop()
        del push
        push = None
    logging.fatal(msg)
    sys.exit(0)


#=================================
#functions
#=================================
def commandHandler(internalid, content):
    """ago command handler"""
    logging.info('commandHandler: %s, %s' % (internalid,content))
    global twitter, push, mail, gtalk, sms
    global client
    command = None

    if content.has_key('command'):
        command = content['command']
    else:
        logging.error('No command specified')
        return None

    #=========================================
    if command=='status':
        #return module status
        try:
            return {'error':0, 'msg':'', 'twitter':twitter.getConfig(), 'mail':mail.getConfig(), 'sms':sms.getConfig(), 'gtalk':gtalk.getConfig(), 'push':push.getConfig()}
        except Exception as e:
            logging.exception('commandHandler: configured exception [%s]' % str(e))
            return {'error':1, 'msg':'Internal error'}

    #=========================================
    elif command=='test':
        if not content.has_key('param1'):
            logging.error('test command: missing parameters')
            return {'error':1, 'msg':'Internal error'}
        type = content['param1']
        if type=='twitter':
            #twitter test
            if twitter.addTweet('agocontrol test tweet @ %s' % time.strftime('%H:%M:%S')):
                return {'error':0, 'msg':'Tweet successful'}
            else:
                logging.error('CommandHandler: failed to tweet')
                return {'error':1, 'msg':'Failed to tweet'}
        elif type=='sms':
            #test sms
            if sms.addSMS(sms.username, 'agocontrol sms test'):
                return {'error':0, 'msg':'SMS sent successfully'}
            else:
                logging.error('CommandHandler: failed to send SMS [%s, %s]' % (str(content['to']), str(content['text'])))
                return {'error':1, 'msg':'Failed to send SMS'}
        elif type=='mail':
            #mail test
            if content.has_key('param2'):
                tos = content['param2'].split(';')
                if mail.addMail(tos, 'agocontrol mail test', 'If you receive this email it means agocontrol alert is working fine!'):
                    return {'error':0, 'msg':'Email sent successfully'}
                else:
                    logging.error('CommandHandler: failed to send email [%s, test]' % (str(tos)))
                    return {'error':1, 'msg':'Failed to send email'}
            else:
                logging.error('commandHandler: parameters missing for SMS')
                return {'error':1, 'msg':'Internal error'}
        elif type=='gtalk':
            #test gtalk
            if gtalk.addMessage(gtalk.username, 'agocontrol gtalk test'):
                return {'error':0, 'msg':'Gtalk message sent succesfully'}
            else:
                logging.error('CommandHandler: failed to send GTalk message [test]')
                return {'error':1, 'msg':'Failed to send GTalk message'}
        elif type=='push':
            #test push
            if push.name=='pushbullet':
                if push.addPush('This is an agocontrol test notification', ''):
                    return {'error':0, 'msg':'Push notification sent'}
                else:
                    logging.error('CommandHandler: failed to send push message with pushbullet [test]')
                    return {'error':1, 'msg':'Failed to send push notification'}
            elif push.name=='pushover':
                if push.addPush('This is an agocontrol test notification'):
                    return {'error':0, 'msg':''}
                else:
                    logging.error('CommandHandler: failed to send push message with pushover [test]')
                    return {'error':1, 'msg':'Failed to send push notification'}
            elif push.name=='notifymyandroid':
                if push.addPush('This is an agocontrol test notification'):
                    return {'error':0, 'msg':''}
                else:
                    logging.error('CommandHandler: failed to send push message with notifymyandroid [test]')
                    return {'error':1, 'msg':'Failed to send push notification'}
        else:
            #TODO add here new alert test
            pass

    #=========================================
    elif command=='sendtweet':
        #send tweet
        if content.has_key('tweet'):
            if twitter.addTweet(content['tweet']):
                return {'error':0, 'msg':''}
            else:
                logging.warning('CommandHandler: failed to tweet [%s]' % str(content['tweet']))
                return {'error':1, 'msg':'Failed to tweet'}
        else:
            logging.error('commandHandler: parameters missing for tweet')
            return {'error':1, 'msg':'Internal error'}
    elif command=='sendsms':
        #send sms
        if content.has_key('text') and content.has_key('to'):
            if sms.addSMS(content['to'], content['text']):
                return {'error':0, 'msg':''}
            else:
                logging.warning('CommandHandler: failed to send SMS [to:%s, text:%s]' % (str(content['to']), str(content['text'])))
                return {'error':1, 'msg':'Failed to send SMS'}
        else:
            logging.error('commandHandler: parameters missing for SMS')
            return {'error':1, 'msg':'Internal error'}
    elif command=='sendmail':
        #send mail
        if content.has_key('to') and content.has_key('subject') and content.has_key('body'):
            tos = content['to'].split(';')
            if mail.addMail(tos, content['subject'], content['body']):
                return {'error':0, 'msg':''}
            else:
                logging.warning('CommandHandler: failed to send email [tos:%s, subject:%s, content:%s]' % (str(tos), str(content['subject']), str(content['body'])))
                return {'error':1, 'msg':'Failed to send email'}
        else:
            logging.error('commandHandler: parameters missing for email')
            return {'error':1, 'msg':'Internal error'}
    elif command=='sendgtalk':
        #send gtalk message
        if content.has_key('to') and content.has_key('message'):
            if gtalk.addMessage(content['to'], content['message']):
                return {'error':0, 'msg':''}
            else:
                logging.warning('CommandHandler: failed to send GTalk message [to:%s, message:%s]' % (str(content['to']), str(content['message'])))
                return {'error':1, 'msg':'Failed to send GTalk message'}
        else:
            logging.error('commandHandler: parameters missing for GTalk')
            return {'error':1, 'msg':'Internal error'}
    elif command=='sendpush':
        #send push
        if push.name=='pushbullet':
            if content.has_key('message'):
                if push.addPush(content['message']):
                    return {'error':0, 'msg':''}
                else:
                    logging.error('CommandHandler: failed to send push message with pushbullet [message:%s file:%s]' % (str(content['message'])))
                    return {'error':1, 'msg':'Failed to send push notification'}
            else:
                logging.error('commandHandler: parameters missing for pushbullet')
                return {'error':1, 'msg':'Internal error'}
        elif push.name=='pushover':
            if content.has_key('message'):
                if push.addPush(content['message']):
                    return {'error':0, 'msg':''}
                else:
                    logging.error('CommandHandler: failed to send push message with pushover [message:%s priority:%s]' % (str(content['message'])))
                    return {'error':1, 'msg':'Failed to send push notification'}
            else:
                logging.error('commandHandler: parameters missing for pushover')
                return {'error':1, 'msg':'Internal error'}
        elif push.name=='notifymyandroid':
            if content.has_key('message'):
                if push.addPush(content['message']):
                    return {'error':0, 'msg':''}
                else:
                    logging.error('CommandHandler: failed to send push message with notifymyandroid [message:%s priority:%s]'% (str(content['message'])))
                    return {'error':1, 'msg':'Failed to send push notification'}
            else:
                logging.error('commandHandler: parameters missing for notifymyandroid')
                return {'error':1, 'msg':'Internal error'}
        else:
            #TODO add here new alert sending
            pass

    #=========================================
    elif command=='setconfig':
        if not content.has_key('param1'):
            logging.error('test command: missing parameters')
            return {'error':1, 'msg':'Internal error'}
        type = content['param1']
        if type=='twitter':
            if not content.has_key('param2'):
                logging.error('test command: missing parameters "param2"')
                return {'error':1, 'msg':'Internal error'}
            accessCode = content['param2'].strip()
            if len(accessCode)==0:
                #get authorization url
                return twitter.getAuthorizationUrl()
            elif len(accessCode)>0:
                #set twitter config
                return twitter.setAccessCode(accessCode)
        elif type=='sms':
            #set sms config
            if content.has_key('param2') and content.has_key('param3'):
                if sms.setConfig(content['param2'], content['param3']):
                    return {'error':0, 'msg':''}
                else:
                    return {'error':1, 'msg':'Unable to save config'}
            else:
                logging.error('commandHandler: parameters missing for SMS config')
                return {'error':1, 'msg':'Internal error'}
        elif type=='mail':
            #set mail config
            if content.has_key('param2') and content.has_key('param3'):
                login = ''
                password = ''
                tls = ''
                if content.has_key('param4'):
                    #format login%_%password
                    try:
                        (login, password) = content['param4'].split('%_%')
                    except:
                        logging.warning('commandHandler: unable to split login%_%password [%s]' % content['param4'])
                if content.has_key('param5'):
                    tls = content['param5']
                if mail.setConfig(content['param2'], content['param3'], login, password, tls):
                    return {'error':0, 'msg':''}
                else:
                    return {'error':1, 'msg':'Unable to save config'}
            else:
                logging.error('commandHandler: parameters missing for Mail config')
                return {'error':1, 'msg':'Internal error'}
        elif type=='gtalk':
            #set gtalk config
            if content.has_key('param2') and content.has_key('param3'):
                if gtalk.setConfig(content['param2'], content['param3']):
                    return {'error':0, 'msg':''}
                else:
                    return {'error':1, 'msg':'Unable to save config'}
            else:
                logging.error('commandHandler: parameters missing for GTalk config')
                return {'error':1, 'msg':'Internal error'}
        elif type=='push':
            #set push config
            if content.has_key('param2'):
                provider = content['param2']
                if provider!=push.name:
                    #destroy existing push
                    push.stop()
                    del push
                    #create new push
                    if provider=='pushbullet':
                        push = Pushbullet('', '')
                    elif provider=='pushover':
                        push = Pushover('')
                    elif provider=='notifymyandroid':
                        push = Notifymyandroid('')
                    else:
                        #TODO add here new provider
                        pass
                if provider=='pushbullet':
                    if content.has_key('param3'):
                        subCmd = content['param3']
                        if subCmd=='getdevices':
                            if content.has_key('param4'):
                                devices = push.getPushbulletDevices(content['param4'])
                                return {'error':0, 'msg':'', 'devices':devices}
                            else:
                                logging.error('commandHandler: parameter "param4" missing for getPushbulletDevices()')
                                return {'error':1, 'msg':'Internal error'}
                        elif subCmd=='save':
                            if content.has_key('param4') and content.has_key('param5'):
                                if push.setConfig(content['param4'], content['param5']):
                                    return {'error':0, 'msg':''}
                                else:
                                    logging.error('Unable to save config')
                                    return {'error':1, 'msg':'Unable to save config'}
                            else:
                                logging.error('commandHandler: parameters missing for Pushbullet config')
                                return {'error':1, 'msg':'Internal error'}
                elif provider=='pushover' or provider=='notifymyandroid':
                    if content.has_key('param3'):
                        if push.setConfig(content['param3']):
                            return {'error':0, 'msg':''}
                        else:
                            logging.error('Unable to save config')
                            return {'error':1, 'msg':'Unable to save config'}
                    else:
                        logging.error('commandHandler: parameter "param3" missing for %s' % provider)
                        return {'error':1, 'msg':'Internal error'}
                else:
                    #TODO add here new provider
                    pass
        else:
            #TODO add here other alert configuration
            pass
    else:
        logging.warning('Unmanaged command "%s"' % content['command'])

def eventHandler(event, content):
    """ago event handler"""
    #logging.info('eventHandler: %s, %s' % (event, content))
    global client
    uuid = None
    internalid = None

    #get uuid
    if content.has_key('uuid'):
        uuid = content['uuid']
        internalid = client.uuidToInternalId(uuid)
    
    if uuid and uuid in client.uuids:
        #uuid belongs to this handler
        #TODO manage events here
        pass


#=================================
#main
#=================================
#init
try:
    #connect agoclient
    client = agoclient.AgoConnection('alert')

    #load config
    configMailSmtp = agoclient.getConfigOption("mail", "smtp", "", 'alert')
    configMailSender = agoclient.getConfigOption("mail", "sender", "", 'alert')
    configMailLogin = agoclient.getConfigOption("mail", "login", "", 'alert')
    configMailPassword = agoclient.getConfigOption("mail", "password", "", 'alert')
    configMailTls = agoclient.getConfigOption("mail", "tls", "", 'alert')
    configTwitterKey = agoclient.getConfigOption("twitter", "key", "", 'alert')
    configTwitterSecret = agoclient.getConfigOption("twitter", "secret", "", 'alert')
    configGTalkUsername = agoclient.getConfigOption("gtalk", "username", "", 'alert')
    configGTalkPassword = agoclient.getConfigOption("gtalk", "password", "", 'alert')
    configSmsUsername = agoclient.getConfigOption("12voip", "username", "", 'alert')
    configSmsPassword = agoclient.getConfigOption("12voip", "password", "", 'alert')
    configPushProvider = agoclient.getConfigOption('push', 'provider', '', 'alert')
    configPushbulletApikey = agoclient.getConfigOption('pushbullet', 'apikey', '', 'alert')
    configPushbulletDevices = agoclient.getConfigOption('pushbullet', 'devices', '', 'alert')
    configPushoverUserid = agoclient.getConfigOption('pushover', 'userid', '', 'alert')
    configNotifymyandroidApikeys = agoclient.getConfigOption('notifymyandroid', 'apikeys', '', 'alert')

    #create objects
    mail = Mail(configMailSmtp, configMailSender, configMailLogin, configMailPassword, configMailTls)
    twitter = Twitter(configTwitterKey, configTwitterSecret)
    sms = SMS12voip(configSmsUsername, configSmsPassword)
    gtalk = GTalk(configGTalkUsername, configGTalkPassword)
    if configPushProvider=='':
        logging.info('Create dummy push')
        push = Dummy()
    elif configPushProvider=='pushbullet':
        push = Pushbullet(configPushbulletApikey, configPushbulletDevices)
    elif configPushProvider=='pushover':
        push = Pushover(configPushoverUserid)
    elif configPushProvider=='notifymyandroid':
        push = Notifymyandroid(configNotifymyandroidApikeys)

    #start services
    mail.start()
    twitter.start()
    sms.start()
    gtalk.start()
    push.start()

    #add client handlers
    client.addHandler(commandHandler)

    #add controller
    logging.info('Add controller')
    client.addDevice('alertcontroller', 'alertcontroller')


except Exception as e:
    #init failed
    logging.exception('Exception during init')
    quit('Init failed, exit now.')

#run agoclient
try:
    logging.info('Running agoalert...')
    client.run()
except KeyboardInterrupt:
    #stopped by user
    quit('agoalert stopped by user')
except Exception as e:
    logging.exception('Exception on main')
    #stop everything
    quit('agoalert stopped')

