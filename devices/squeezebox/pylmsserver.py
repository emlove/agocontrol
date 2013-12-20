#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
PyLMS: Python Wrapper for Logitech Media Server CLI
(Telnet) Interface

Copyright (C) 2013 Tang <tanguy [dot] bonneau [at] gmail [dot] com>

LMSServer class is based on JingleManSweep <jinglemansweep [at] gmail [dot] com>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import telnetlib
import urllib
from pylmsplayer import Player
import threading
import logging
import time

class LMSServer(object):

    """
    LMS Server access to perform some requests
    """

    def __init__(self, hostname="localhost", port=9090, 
                       username="", password="",
                       charset="utf-8"):
        """
        Constructor
        """
        self.debug = False
        self.logger = logging.getLogger("LMSServer")
        self.telnet = None
        self.logged_in = False
        self.hostname = hostname
        self.port = port
        self.username = username
        self.password = password
        self.version = ""
        self.player_count = 0
        self.players = []
        self.charset = charset

    def __del__(self):
        """
        Destructor
        """
        self.disconnect()
    
    def connect(self, update=True):
        """
        Connect
        """
        if self.telnet_connect():
            if self.login():
                self.get_players(update=update)
            else:
                self.telnet = None
                self.logger.debug('Login failed')
                return False
        else:
            self.telnet = None
            return False
        return True
        
    def disconnect(self):
        """
        Disconnect
        """
        if self.telnet:
            self.telnet.close()
            
    def is_connected(self):
        """
        is connected?
        """
        if self.telnet:
            return True
        else:
            return False
        
    def telnet_connect(self):
        """
        Telnet Connect
        """
        try:
            self.telnet = telnetlib.Telnet(self.hostname, self.port)
        except Exception as e:
            self.logger.critical('Unable to connect [%s]' % str(e))
            self.telnet = None
        return self.telnet
    
    def login(self):
        """
        Login
        """
        result = self.request("login %s %s" % (self.username, self.password))
        self.logged_in = (result == "******")
        return self.logged_in

    def response(self, timeout=0):
        """
        Response: wait for something on telnet socket
        timeout: wait until timeout
        """
        resp = None
        try:
            if self.is_connected():
                resp = self.telnet.read_until( '\n'.encode(self.charset), timeout)
            else:
                resp = None
        except EOFError:
            #telnet failed (not connected?)
            self.telnet = None #force to reconnect next time
            resp = None
        except Exception as e:
            #something failed
            self.logger.error(str(e))
            resp = None
        return resp

    def request(self, command, decode_output=True):
        """
        Request
        command_string : command to send
        preserver_encoding : preserve encoding in result
        timeout : unblock telnet command after specified seconds
        """
        try:
            #connect if necessary
            if not self.telnet:
                if not self.connect():
                    #failed to connect
                    raise Exception('Unable to connect')

            #process command line
            self.logger.debug('command="%s"' % command)
            command = command.strip()
            command_len = len( command.strip().split(' ') )
            if command.endswith(u'?'):
                command_len -= 1
            command_encoded = (command.strip()).encode(self.charset)

            #send command
            self.telnet.write( command_encoded + '\n'.encode(self.charset) )
            response = self.telnet.read_until( '\n'.encode(self.charset) )
            response = response.strip()
            self.logger.debug('response="%s"' % response)

            #process response
            response_parts = response.split(' ')
            response_len = len(response.split(' '))
            self.logger.debug('command_parts=%d' % command_len)
            self.logger.debug('response_parts=%d' % response_len)
        
            #process result
            result = ''
            for i in range(command_len, response_len):
                if decode_output:
                    result += self._decode(response_parts[i]) + u' '
                else:
                    result += unicode(response_parts[i]) + u' '
            result = result.strip()
            self.logger.debug('result="%s"' % result)
        
        except EOFError:
            #telnet failed (not connected?)
            self.logger('EOFError: telnet failed')
            self.telnet = None #force to reconnect next time
            result = None

        except Exception as e:
            #something failed
            self.logger.error(str(e))
            result = None

        return result
        

    def request_with_results(self, command):
        """
        Request with results
        Return tuple (count, results, error_occured)
        """
        count = 0
        items = []
        try:
            #request command without decoding output
            response = self.request(command, False)
            response_parts = response.split(' ')
            if response.startswith('count'):
                self.logger.debug('count response')
                #get number of items
                count = int(self._decode(response_parts[0]).split(':',1)[1])

                #get items separator
                separator = self._decode(response_parts[1]).split(':',1)[0]

                #get items
                sub_items = None
                for i in range(1, len(response_parts)):
                    (key,val) = self._decode(response_parts[i]).split(':',1)
                    if key==separator:
                        #save current sub_items
                        if sub_items:
                            items.append(sub_items)
                        sub_items = {}
                        sub_items[key] = val
                    else:
                        sub_items[key] = val
                items.append(sub_items)
                self.logger.debug(items)

            else:
                self.logger.debug('no count response')
                #just split items
                sub_items = {}
                count = 1
                for i in range(len(response_parts)):
                    (key,val) = self._decode(response_parts[i]).split(':',1)
                    sub_items[key] = val
                items.append(sub_items)

        except Exception as e:
            #error parsing results (not correct?)
            self.logger.error('Exception occured in request_with_results: %s' % str(e))
            return 0,[],True

        return count, items, False

    def get_players(self, update=True):
        """
        Get Players
        """
        self.players = []
        player_count = self.get_player_count()
        for i in range(player_count):
            player = Player(server=self, index=i-1, update=update)
            self.players.append(player)
        return self.players

    def get_player(self, ref):
        """
        Get Player
        """
        ref = str(ref).lower()
        self.logger.debug('ref="%s"' % ref)
        if ref:
            for player in self.get_players():
                player_name = str(player.name).lower()
                player_mac = str(player.mac).lower()
                self.logger.debug('compare %s==%s or in %s' % (ref, player_mac, player_name))
                if ref==player_mac or ref in player_name:
                    return player
        return None

    def get_version(self):
        """
        Get Version
        """
        self.version = self.request("version ?")
        return self.version
    
    def get_player_count(self):
        """
        Get Number Of Players
        """
        self.player_count = self.request("player count ?")
        return int(self.player_count)

    def search(self, term, mode='albums'):
        """
        Search term in database
        """
        if mode=='albums':
            return self.request_with_results("albums 0 50 tags:%s search:%s" % ("l", term))
        elif mode=='songs':
            return self.request_with_results("songs 0 50 tags:%s search:%s" % ("", term))
        elif mode=='artists':
            return self.request_with_results("artists 0 50 search:%s" % (term))

    def rescan(self, mode='fast'):
        """
        Rescan library
        Mode can be 'fast' for update changes on library, 'full' for complete library scan and 'playlists' for playlists scan only
        """
        is_scanning = True
        try:
            is_scanning = bool(self.request("rescan ?"))
        except:
            pass
        
        if not is_scanning:
            if mode=='fast':
                return self.request("rescan")
            elif mode=='full':
                return self.request("wipecache")
            elif mode=='playlists':
                return self.request("rescan playlists")
        else:
            return ""
        
    def rescanprogress(self):
        """
        Return current rescan progress
        """
        return self.request_with_results("rescanprogress")
    
    def _decode(self, string):
        return urllib.unquote_plus(string).encode(self.charset)



class LMSServerNotifications(threading.Thread, LMSServer):
    """
    Class that catch LMS server notifications to create events on some server actions
    """
    def __init__(self, notifications_callback, hostname="localhost", port=9090, username="", password="", charset="utf-8"):
        """constructor"""
        LMSServer.__init__(self, hostname, port, username, password, charset)
        threading.Thread.__init__(self)
        self.logger = logging.getLogger("LMSServerNotifications")
        
        #members
        self.__running = True
        self._player_ids = []
        self._callback = notifications_callback
        
    def __del__(self):
        """Destructor"""
        self.stop()
        LMSServer.__del__(self)

    def stop(self):
        """stop process"""
        self.__running = False
            
    def subscribe_players(self, player_ids):
        """subscribe players to notifications"""
        if not player_ids:
            self._player_ids = []
        elif type(player_ids) is list:
            self.logger.warning('player_ids must be a list')
            self._player_ids = player_ids
        else:
            self._player_ids = []

    def _process_response(self, items):
        """process response received by lmsserver
           this function can be overwriten to process some other stuff"""
        self._callback(items)

    def run(self):
        """process"""
        while self.__running:
            if not self.is_connected():
                #connect pylmsserver
                if self.connect():
                    #subscribe to notifications
                    self.request('listen 1')
        
            if self.is_connected():
                response = self.response(timeout=1)
    
                if response:
                    #there is something
                    #self.logger.debug('RAW=%s' % response.strip())
                    
                    #split response
                    items = response.split(' ')
                    #and unquote all items
                    for i in range(len(items)):
                        items[i] = urllib.unquote(items[i].strip())

                    #finally process response
                    if self._player_ids:
                        if items[0] in self._player_ids:
                            #notifications for specified player
                            self._process_response(items)
                    else:
                        #no player id filter
                        self._process_response(items)
            else:
                #pause
                time.sleep(1)






"""TESTS"""
if __name__=="__main__":
    import gobject; gobject.threads_init()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_sh = logging.StreamHandler()
    console_sh.setLevel(logging.DEBUG)
    console_sh.setFormatter(logging.Formatter('%(asctime)s %(name)-20s %(levelname)-8s %(message)s'))
    logger.addHandler(console_sh)
    notif = None

    def notifications(items):
        logger.info(items)

    try:
        server = LMSServer('192.168.1.53', 9090)
        p = server.get_player('00:04:20:12:47:33')
        logger.info(p)

        #notif = LMSServerNotifications(notifications, '192.168.1.53', 9090)
        #notif.start()
        mainloop = gobject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        logger.debug('====> KEYBOARD INTERRUPT <====')
        logger.debug('Waiting for threads to stop...')
        mainloop.quit()
#notif.stop()
