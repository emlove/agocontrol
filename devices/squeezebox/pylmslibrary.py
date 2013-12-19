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

from pylmsserver import LMSServer
import threading
import os
import logging
import urllib

class CacheCovers(threading.Thread):
    """cache covers for thumbnails"""

    def __init__(self, server_ip, server_port, cover_path, albums, end_callback=None):
        """init"""
        threading.Thread.__init__(self)
        self.logger = logging.getLogger("CacheCovers")
        self.albums = albums
        self.cover_path = cover_path
        self.server_port = server_port
        self.server_ip = server_ip
        self.running = True
        self.end_callback = end_callback
        
    def stop(self):
        """stop process"""
        self.running = False
        
    def start(self):
        """start process"""
        self.logger.debug('CacheCovers started')
        for album in self.albums:
            if not album.has_key('id'):
                self.logger.warning('Album has no Id !?!?')
            elif not album.has_key('artwork_track_id'):
                self.logger.warning('Album "%s" has no artwork_track_id field' % album['id'])
            else:
                url = 'http://%s:%d/music/%s/cover_100x100.png' % (self.server_ip, self.server_port, album['artwork_track_id'])
                path = os.path.join(self.cover_path, '%s_%s.png' % (album['id'], album['artwork_track_id']))
                #self.logger.debug('New cover : url=%s cover=%s' % (url, path))
                if not os.path.exists(path):
                    #cover not exists
                    fil = open(path, 'wb')
                    bin = urllib.urlopen(url)
                    fil.write(bin.read())
                    fil.close()
            
            #stop statement?
            if not self.running:
                break
        self.logger.debug('CacheCovers stopped')

        
       
        
        
        
        
class LMSLibrary():
    LIBRARY_EMPTY = 0
    LIBRARY_UPTODATE = 1
    LIBRARY_UPDATING = 2

    def __init__(self, server_ip, server_port=9090, server_user='', server_password=''):
        """constructor"""
        #init
        self.logger = logging.getLogger("Library")
        
        #members
        self.server_ip = server_ip
        self.server_port = server_port
        self.__cover_path = os.path.join(os.path.expanduser('~'), '.squeezedesktop', 'cache')
        if not os.path.exists(self.__cover_path):
            #create cache directory
            os.makedirs(self.__cover_path)
        self.__server_infos_path = os.path.join(os.path.expanduser('~'), '.squeezedesktop', 'server.conf')
        self.__albums_count = 0
        self.__artists_count = 0
        self.__genres_count = 0
        self.__years_count = 0
        
        #objects
        self.server = LMSServer(server_ip, server_port, server_user, server_password)
        self.server.connect()
        self.cache_covers = None
        
    def __del__(self):
        """destructor"""
        #only stop threads if runnings
        if self.cache_covers:
            self.cache_covers.stop()
            
    def get_albums(self):
        """return all albums"""
        #     id 	Album ID. Item delimiter.
        #l 	  album 	Album name, including the server's added "(N of M)" if the server is set to group multi disc albums together. See tag "title" for the unmodified value.
        #y 	  year 	Album year. This is determined by the server based on the album tracks.
        #j 	  artwork_track_id 	Identifier of one of the album tracks, used by the server to display the album's artwork.
        #t 	  title 	"Raw" album title as found in the album tracks ID3 tags, as opposed to "album". Note that "title" and "album" are identical if the server is set to group discs together.
        #i 	  disc 	Disc number of this album. Only if the server is not set to group multi-disc albums together.
        #q 	  disccount 	Number of discs for this album. Only if known.
        #w 	  compilation 	1 if this album is a compilation.
        #a 	  artist 	The album artist (depends on server configuration).
        #S 	  artist_id 	The album artist id (depends on server configuration).
        #s 	  textkey 	The album's "textkey" is the first letter of the sorting key.
        #X 	  album_replay_gain 	The album's replay-gain. 
        #need at least j tag to find associated cover in cache
        count, items, error = self.server.request_with_results('albums 0 %d tags:lj' % self.__albums_count)
        if error:
            return None
        else:
            return items
            
    def get_album(self, id):
        """return album infos"""
        if id!=None:
            count, items, error = self.server.request_with_results('albums 0 1 album_id:%d tags:ljyS' % id)
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_album_songs(self, id):
        """return all songs from specified album id"""
        # rescan 	Returned with value 1 if the server is still scanning the database. The results may therefore be incomplete. Not returned if no scan is in progress.
        #    count 	Number of results returned by the query, that is, total number of elements to return for this song.
        #    id 	Track ID.
        #    title 	Song title
        #a 	artist 	Artist name.
        #A 	<role> 	For every artist role (one of "artist", "composer", "conductor", "band", "albumartist" or "trackartist"), a comma separated list of names.
        #B 	buttons 	A hash with button definitions. Only available for certain plugins such as Pandora.
        #c 	coverid 	coverid to use when constructing an artwork URL, such as /music/$coverid/cover.jpg
        #C 	compilation 	1 if the album this track belongs to is a compilation
        #d 	duration 	Song duration in seconds.
        #e 	album_id 	Album ID. Only if known.
        #f 	filesize 	Song file length in bytes. Only if known.
        #g 	genre 	Genre name. Only if known.
        #G 	genres 	Genre names, separated by commas (only useful if the server is set to handle multiple items in tags).
        #i 	disc 	Disc number. Only if known.
        #I 	samplesize 	Song sample size (in bits)
        #j 	coverart 	1 if coverart is available for this song. Not listed otherwise.
        #J 	artwork_track_id 	Identifier of the album track used by the server to display the album's artwork. Not listed if artwork is not available for this album.
        #k 	comment 	Song comments, if any.
        #K 	artwork_url 	A full URL to remote artwork. Only available for certain plugins such as Pandora and Rhapsody.
        #l 	album 	Album name. Only if known.
        #L 	info_link 	A custom link to use for trackinfo. Only available for certain plugins such as Pandora.
        #m 	bpm 	Beats per minute. Only if known.
        #M 	musicmagic_mixable 	1 if track is mixable, otherwise 0.
        #n 	modificationTime 	Date and time song file was last changed on disk.
        #N 	remote_title 	Title of the internet radio station.
        #o 	type 	Content type. Only if known.
        #p 	genre_id 	Genre ID. Only if known.
        #P 	genre_ids 	Genre IDs, separated by commas (only useful if the server is set to handle multiple items in tags).
        #D 	addedTime 	Date and time song file was first added to the database.
        #U 	lastUpdated 	Date and time song file was last updated in the database.
        #q 	disccount 	Number of discs. Only if known.
        #r 	bitrate 	Song bitrate. Only if known.
        #R 	rating 	Song rating, if known and greater than 0.
        #s 	artist_id 	Artist ID.
        #S 	<role>_ids 	For each role as defined above, the list of ids.
        #t 	tracknum 	Track number. Only if known.
        #T 	samplerate 	Song sample rate (in KHz)
        #u 	url 	Song file url.
        #v 	tagversion 	Version of tag information in song file. Only if known.
        #w 	lyrics 	Lyrics. Only if known.
        #x 	remote 	If 1, this is a remote track.
        #X 	album_replay_gain 	Replay gain of the album (in dB), if any
        #y 	year 	Song year. Only if known.
        #Y 	replay_gain 	Replay gain (in dB), if any 
        if id!=None:
            count, items, error = self.server.request_with_results('songs 0 200 album_id:%deJ' % id)
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_artists(self):
        """return all artists"""
        #   id 	Artist ID. Item delimiter.
        #   artist 	Artist name.
        #s 	  textkey 	The artist's "textkey" is the first letter of the sorting key. 
        count, items, error = self.server.request_with_results('artists 0 %d' % self.__artists_count)
        if error:
            return None
        else:
            return items
            
    def get_artist(self, id):
        """return artist infos"""
        if id!=None:
            count, items, error = self.server.request_with_results('artists 0 1 artist_id:%d' % id)
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_artist_albums(self, id):
        """return albums from specified artist id"""
        if id!=None:
            count, items, error = self.server.request_with_results('albums 0 %d artist_id:%d tags:ljyS' % (self.__albums_count, id))
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_genres(self):
        """return all genres"""
        count, items, error = self.server.request_with_results('genres 0 %d' % self.__genres_count)
        if error:
            return None
        else:
            return items
            
    def get_genre(self, id):
        """return genre infos"""
        if id!=None:
            count, items, error = self.server.request_with_results('genre 0 1 genre_id:%d' % id)
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_genre_albums(self, id):
        """return albums from specified genre id"""
        if id!=None:
            count, items, error = self.server.request_with_results('albums 0 %d genre_id:%d tags:ljyS' % (self.__albums_count, id))
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_years(self):
        """return all years"""
        count, items, error = self.server.request_with_results('years 0 %d' % self.__years_count)
        if error:
            return None
        else:
            return items
            
    def get_year_albums(self, id):
        """return albums from specified year id"""
        if id!=None:
            count, items, error = self.server.request_with_results('albums 0 %d year:%d tags:ljyS' % (self.__albums_count, id))
            if error:
                return None
            else:
                return items
        else:
            return None
            
    def get_song_infos(self, id):
        """return full song infos"""
        if id!=None:
            count, items, error = self.server.request_with_results('songinfo 0 50 track_id:%d tags:adefgIJlnortTuvyY' % id)
            if not error and count==1:
                return items[0]
            else:
                return None
        else:
            return None
            
    def get_song_infos_by_url(self, url):
        """return full song infos"""
        if id!=None:
            count, items, error = self.server.request_with_results('songinfo 0 50 url:%s tags:adefgIJlnortTuvyY' % url)
            self.logger.debug('count=%d' % count)
            self.logger.debug('items=%s' % str(items))
            self.logger.debug('error=%s' % str(error))
            if not error and count==1:
                return items[0]
            else:
                return None
        else:
            return None
        
            
    def get_cover_path(self, album_id, artwork_track_id):
        """return cover"""
        cover_path = None
        
        if album_id and artwork_track_id:
            cover_path = os.path.join(self.__cover_path, '%s_%s.png' % (album_id, artwork_track_id))
            self.logger.debug('Cover path:%s' % cover_path)
            if not os.path.exists(cover_path):
                #cover doesn't exists
                self.logger.debug('Cover doesn\'t exist!')
                cover_path = None
        
        return cover_path
        
    def search(self, term):
        """search something on database"""
        #TODO
        pass
        
    def check_update(self):
        """check if library needs update, return True if database needs update followed by number of albums, artists, and genres"""
        #get stats
        lms_genres_count = int(self.server.request('info total genres ?'))
        self.__genres_count = lms_genres_count
        lms_artists_count = int(self.server.request('info total artists ?'))
        self.__artists_count = lms_artists_count
        lms_albums_count = int(self.server.request('info total albums ?'))
        self.__albums_count = lms_albums_count
        self.logger.debug('LMS total artists=%d albums=%d genres=%d' % (lms_artists_count, lms_albums_count, lms_genres_count))
        
        #check if fresh install
        if not os.path.exists(self.__server_infos_path):
            #conf file doesn't exist create empty one
            conf = open(self.__server_infos_path, 'w')
            conf.write('albums:0\nartists:0\ngenres:0')
            local_genres_count = 0
            local_artists_count = 0
            local_albums_count = 0
        else:
            #read from file
            conf = open(self.__server_infos_path, 'r')
            for line in conf.readlines():
                if line.startswith('artists'):
                    try:
                        local_artists_count = int(line.split(':')[1].strip())
                    except:
                        local_artists_count = 0
                elif line.startswith('albums'):
                    try:
                        local_albums_count = int(line.split(':')[1].strip())
                    except:
                        local_albums_count = 0
                elif line.startswith('genres'):
                    try:
                        local_genres_count = int(line.split(':')[1].strip())
                    except:
                        local_genres_count = 0
                        
            #compare results
            self.logger.debug('%d==%d %d==%d %d==%d' % (lms_genres_count, local_genres_count, lms_artists_count, local_artists_count, lms_albums_count, local_albums_count))
            if lms_genres_count!=local_genres_count or lms_artists_count!=local_artists_count or lms_albums_count!=local_albums_count:
                #need update
                self.logger.debug('Need update')
                self.__cache_covers(lms_albums_count)
                    
    def __cache_covers(self, albums_count):
        """cache covers for thumbnails"""
        count, albums, error = self.server.request_with_results('albums 0 %d tags:j' % albums_count)
        if not error:
            self.logger.debug('Updating...')
            self.cache_covers = CacheCovers(self.server_ip, self.server_port, self.__cover_path, albums)
            self.cache_covers.start()
        else:
            #error
            self.logger.error('Unable to get albums list')
        

"""TESTS"""
if __name__=="__main__":
    import gobject; gobject.threads_init()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    console_sh = logging.StreamHandler()
    console_sh.setLevel(logging.DEBUG)
    console_sh.setFormatter(logging.Formatter('%(asctime)s %(name)-20s %(levelname)-8s %(message)s'))
    logger.addHandler(console_sh)
    
    try:
        lib = LMSLibrary('192.168.1.53', 9090)
        infos = lib.get_song_infos_by_url('file:///media/raid/mp3/J/Joseph%20Arthur%20-%202013%20-%20Ballad%20Of%20Boogie%20Christ/03%20-%20The%20Ballad%20Of%20Boogie%20Christ.mp3')
        logger.info(infos)
        #lib.check_update()
        #mainloop = gobject.MainLoop()
        #mainloop.run()
    except KeyboardInterrupt:
        logger.debug('====> KEYBOARD INTERRUPT <====')
        logger.debug('Waiting for threads to stop...')
        #mainloop.quit()
