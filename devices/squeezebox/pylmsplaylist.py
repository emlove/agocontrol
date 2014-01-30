#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
PyLMS: Python Wrapper for Logitech Media Server CLI (Telnet) Interface
 
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

from pylmsserver import LMSServer, LMSServerNotifications
from pylmslibrary import LMSLibrary
import threading
import os
import logging
import urllib
import time

class LMSPlaylist(LMSServerNotifications):
    """Manage playlist"""

    FILTER_TIMEOUT = 10 #in ms
    ALLOWED_COMMANDS = ['playlist', 'power', 'play', 'pause']

    def __init__(self, library, hostname='localhost', port=9090, username='', password='', charset='utf8'):
        """init"""
        LMSServerNotifications.__init__(self, self._callback, hostname, port, username, password, charset)
        self.logger = logging.getLogger("LMSPlaylist")

        #objects
        #create new LMSServer to perform independant request
        self.__server = LMSServer(hostname, port, username, password)
        
        #members
        self.running = True
        self.library = library
        self.__lastresponse = {}
        self.__play_callback = None
        self.__pause_callback = None
        self.__stop_callback = None
        self.__addtrack_callback = None
        self.__deltrack_callback = None
        self.__movetrack_callback = None
        self.__reload_callback = None

    def __millitime(self):
        return int(round(time.time() * 1000))

    def _callback(self):
        #nothing to do here, everything is done in overwritten method _process_response
        pass

    def __filterByTimestamp(self, player_id):
        """Filter response by timestamp
            return True if response must be filtered"""
        msec = self.__millitime()
        if self.__lastresponse.has_key(player_id):
            if msec<(self.__lastresponse[player_id] + self.FILTER_TIMEOUT):
                #forget response
                return True
            else:
                #update last response time
                self.__lastresponse[player_id] = msec
        else:
            #save current response time
            self.__lastresponse[player_id] = msec
        return False

    def __filterByResponse(self, command):
        """Filter response by command
            return True if response must be filtered"""
        if not command in self.ALLOWED_COMMANDS:
            return True
        else:
            return False
        
    def _process_response(self, items):
        """overwrite _process_reponse from LMSServerNotifications
           process response received by lmsserver
           this function can be overwriten to process some other stuff"""
        self.logger.debug('-->_process_response %s' % str(items))

        try:
            #filter response
            if self.__filterByResponse(items[1]):
                #don't process response
                self.logger.debug('  ---> response kicked')
                return None

            if items[1]=='playlist':
                if items[2]=='newsong':
                    #192.168.1.1 playlist newsong Thinking%20Of%20You%20(Flo%20Rida) 20
                    #player starts playing a new song
                    if self.__play_callback:
                        self.__play_callback(items[0], items[3], items[4])
                elif items[2]=='pause':
                    #192.168.1.1 pause [0|1]
                    #player update pause status
                    if len(items)==4:
                        if items[3]=='1':
                            #player is paused
                            if self.__pause_callback:
                                self.__pause_callback(items[0])
                        else:
                            #player is playing
                            if self.__play_callback:
                                self.__play_callback(items[0], '', '')
                    else:
                        #player is paused
                        if self.__pause_callback:
                            self.__pause_callback(items[0])
                elif items[2]=='addtracks':
                    #192.168.1.1 playlist addtracks track.id=274336 index:40
                    #new track added in playlist
                    if self.__addtrack_callback:
                        self.__addtrack_callback(items[0], items[3], items[4].replace('index:', ''))
                elif items[2]=='delete':
                    #192.168.1.1 playlist delete 0
                    #new track added in playlist
                    if self.__deltrack_callback:
                        self.__deltrack_callback(items[0], items[3])
                elif items[2]=='stop':
                    #192.168.1.1 playlist stop
                    #player stopped
                    if self.__stop_callback:
                        self.__stop_callback(items[0])
                elif items[2]=='loadtracks':
                    #192.168.1.1 playlist loadtracks track.id%3D243510    index%3A0
                    #playlist reloaded
                    if self.__reload_callback:
                        self.__reload_callback(items[0])
                elif items[2]=='':
                    #192.168.1.1 playlist move 24 23
                    #track moved in playlist
                    if self.__movetrack_callback:
                        self.__movetrack_callback(items[0], int(items[3]), int(items[4]))

            elif items[1]=='pause':
                #00:04:20:12:47:33 pause
                if self.__pause_callback:
                    self.__pause_callback(items[0])

            elif items[1]=='play':
                #00:04:20:12:47:33 play
                if self.__play_callback:
                    self.__play_callback(items[0], '', '')

            elif items[1]=='power':
                if items[2]=='1':
                    #00:04:20:12:47:33 power 1
                    #player is on
                    if self.__on_callback:
                        self.__on_callback(items[0])
                elif items[2]=='0':
                    #00:04:20:12:47:33 power 0
                    #player is off
                    if self.__off_callback:
                        self.__off_callback(items[0])
        except Exception as e:
            self.logger.error('Exception in _process_response: %s' % str(e))
        
    def set_callbacks(self, play_callback, pause_callback, stop_callback, on_callback, off_callback, addtrack_callback, deltrack_callback, movetrack_callback, reload_callback):
        """callbacks:
        play_callback: player starts playing
        pause_callback: player playback is paused
        stop_callback: player stops playing
        addtrack_callback: new track added to playlist
        deltrack_callback: track deleted from playlist
        movetrack_callback : track moved on playlist
        reload_callback: playlist reloaded
        on_callback: player switched on
        off_callback: player switched off
        """
        self.__play_callback = play_callback
        self.__pause_callback = pause_callback
        self.__stop_callback = stop_callback
        self.__addtrack_callback = addtrack_callback
        self.__deltrack_callback = deltrack_callback
        self.__movetrack_callback = movetrack_callback
        self.__reload_callback = reload_callback
        self.__on_callback = on_callback
        self.__off_callback = off_callback
        
    def get_playlist(self, player_id):
        """return full playlist content"""
        playlist = []
        
        #get number of item in playlist
        self.logger.debug('request')
        count = 0
        try:
            count = int(self.__server.request('%s playlist tracks ?' % player_id))
        except Exception as e:
            self.logger.fatal('Failed to get playlist songs count: %s' % str(e))
            count = 0
        self.logger.debug('playlist count=%d' % count)
        
        #get current song
        current_song = 0
        try:
            current_song = int(self.__server.request('%s playlist index ?' % player_id))
        except Exception as e:
            self.logger.fatal('Failed to get current song index: %s' % str(e))
            current_song = 0
        self.logger.debug('current_song=%d' % current_song)
        
        #get songs infos one by one
        self.logger.debug('player_id=%s' % player_id)
        for i in range(count):
            try:
                count, url, error = self.__server.request_with_results('%s playlist path %d ?' % (player_id, i))
                if not error:
                    url = '%s%s' % ('file:',url[0]['file'])
                    #self.logger.debug('url=%s' % url)
                    song = self.library.get_song_infos_by_url(url)
                    #add current song info
                    if i==current_song:
                        song.update({'current':True})
                    else:
                        song.update({'current':False})
                    playlist.append( song )
            except Exception, e:
                #problem during song infos retrieving
                self.logger.error('Unable to get song infos: %s' % str(e))
        
        return playlist
        
    def get_current_song(self, player_id):
        """return current song infos"""
        current = None
        
        try:
            index = int(self.__server.request('%s playlist index ?' % player_id))
            song = self.__server.request('%s playlist path %d ?' % (player_id, index))
            self.logger.debug('song=%s' % song)
            if song:
                #url = '%s%s' % ('file:',song[0]['file'])
                #self.logger.debug('url=%s' % url)
                current = self.library.get_song_infos_by_url(song)
            else:
                #error occured
                self.logger.error('Unable to get current song on player %s' % player_id)
        except Exception as e:
            #problem during song infos retrieving
            self.logger.error('Unable to get current song infos: %s' % str(e))
            
        return current

    def get_server(self):
        """return server to request some stuff"""
        return self.__server

        
"""TESTS"""
if __name__=="__main__":
    import gobject; gobject.threads_init()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_sh = logging.StreamHandler()
    console_sh.setLevel(logging.DEBUG)
    console_sh.setFormatter(logging.Formatter('%(asctime)s %(name)-20s %(levelname)-8s %(message)s'))
    logger.addHandler(console_sh)
    play = None
    lib = None
    
    def check_field(field, song):
        if song.has_key(field):
            return song[field]
        else:
            logger.info('Song has no field "%s" [%s]' % (field, song))
            return ''

    def get_current_song(playlist, player):
        song = playlist.get_current_song(player)
        artist = check_field('artist', song)
        title = check_field('title', song)
        album = check_field('album', song)
        year = check_field('year', song)
        logger.info('==> current song: %s (%s, %s, %s)' % (title, artist, album, year))
        
    def current_song_changed(player, title, index):
        song = play.get_current_song(player)
        if song:
            cover = '[no cover]'
            logger.debug('song=%s' % str(type(song)))
            if lib.get_cover_path(song['album_id'], song['artwork_track_id']):
                cover = '[cover]'
            artist = check_field('artist', song)
            title = check_field('title', song)
            album = check_field('album', song)
            year = check_field('year', song)
            logger.info('==> song changed on "%s": %s (%s, %s, %s) %s' % (player, title, artist, album, year, cover))
        else:
            logger.error('No song!')
    
    try:
        lib = LMSLibrary('192.168.1.53', 9090)
        play = LMSPlaylist(lib, '192.168.1.53', 9090)
        play.set_callbacks(current_song_changed, None, None, None, None, None, None, None, None)
        play.start()
        player_id = '00:04:20:1e:10:42'

        s=play.get_server()
        for p in s.get_players():
            logger.info(' ===> %s on? %s' % (p.get_mac(), str(p.get_is_on())))

        #get playlist
        """songs = play.get_playlist(player_id)
        i = 0
        logger.info('PLAYLIST:')
        for song in songs:
            current_song = ''
            if song['current']:
                current_song = '*'
            logger.info(' - song#%02d %s : %s (%s, %s, %s)'% (i, current_song, song['title'], song['artist'],song['album'], song['year']))
            i += 1"""

        #get current song
        #gobject.timeout_add(30000, get_current_song, play, player_id)
        #play.get_current_song(player_id)

        mainloop = gobject.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        logger.debug('====> KEYBOARD INTERRUPT <====')
        logger.debug('Waiting for threads to stop...')
        play.stop()
        mainloop.quit()


