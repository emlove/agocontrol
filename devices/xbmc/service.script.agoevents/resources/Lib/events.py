'''
	AGOControl Event Engine for XBMC
	Copyright (C) 2013 Jeroen Simonetti

	Based on work from ISY-event script from https://code.google.com/p/isy-events/

	LICENSE:
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 2 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
   
	DESCRIPTION:
	This XBMC addon sends events from xbmc player status into agocontrol.

	This file was based on work done by Ryan M. Kraus (https://code.google.com/p/isy-events/)
   
	WRITTEN:	01/2013
'''

# CONSTANTS
__author__ = 'Jeroen Simonetti'
__version__ = '0.1.0'
__url__ = 'https://www.agocontrol.com/'

# xbmc
import xbmc

from qpid.messaging import *
from qpid.util import URL
from qpid.log import enable, DEBUG, WARN

import myCollections as mc

class xbmcEvents(object):

	# settings
	_wait = 0.5

	# current status
	_playingMovie = mc.histlist(False)
	_playingMusic = mc.histlist(False)
	_time = mc.histlist(-1.0)
	_paused = mc.histlist(False)

	content = {}

	def RaiseEvent(self, event):
		self.content["new_state"] = event
		message = Message(subject="event.mediaplayer.statechanged", content=self.content)
		self.sender.send(message)

	def RunMainLoop(self, wait):
		# set loop wait time
		self._wait = wait
  
 
		# connect to xbmc
		player = xbmc.Player()
   
		# raise xbmc started event
		self.RaiseEvent('Player.Start')


		while (not xbmc.abortRequested):
			# check movie playing status
			self._playingMovie.set(player.isPlayingVideo())
		   
			# check music playing status
			self._playingMusic.set(player.isPlayingAudio())
		   
			# check paused status
			try:
				self._time.set(player.getTime())
				self._paused.set(not self._time.delayed_step(3) and self._time.get(1) > -1 and self._time.get(2) > -1)
			except Exception:
				self._paused.set(False)
				self._time.set(-1.0)
				   
			# check for events
			if self._playingMovie.step_on():
				# raise started playing movie
				self.RaiseEvent('Movie.Play')
			elif self._playingMovie.step_off():
				# raise stopped playing movie
				self.RaiseEvent('Movie.Stop')
			elif self._paused.step_on() and self._playingMovie.get():
				# raise movie paused
				self.RaiseEvent('Movie.Pause')
			elif self._paused.step_off() and self._playingMovie.get():
				# raise movie resumed
				self.RaiseEvent('Movie.Resume')
		   
			elif self._playingMusic.step_on():
				# raise started playing music
				self.RaiseEvent('Music.Play')
			elif self._playingMusic.step_off():
				# raise stopped playing music
				self.RaiseEvent('Music.Stop')
			elif self._paused.step_on() and self._playingMusic.get():
				# raise music paused
				self.RaiseEvent('Music.Pause')
			elif self._paused.step_off() and self._playingMusic.get():
				# raise music resumed
				self.RaiseEvent('Music.Resume')
		   
			# wait sleep time
			# time.sleep(self._wait)
			xbmc.sleep(int(self._wait * 1000))
		# raise xbmc quit event
		self.RaiseEvent('Player.End')

