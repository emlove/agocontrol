#
# Squeezebox client
#
# copyright (c) 2013 James Roberts <jimbob@jamesroberts.co.uk>
#

import httplib
import json

class SqueezeboxServer:
	def __init__(self, server):
		self.server = server
		
		# Power commands - status not used at present.
		# Could be refactored here enabling easy addition of many commands
		self.powerCommand = { "on": "1", "off": "0", "status": "?" }
		
		self.connection = httplib.HTTPConnection(server)
		self.headers = {'Content-type': 'application/json'}
		
	def sendRequest(self, data):
		self.data = data
		self.params = json.dumps(self.data)
		
		self.connection.request('POST', "/jsonrpc.js", self.params, self.headers)
		self.response = self.connection.getresponse()
		#print ("Status=%s, Reason=%s" % (self.response.status, self.response.reason))

		self.data  = self.response.read()
		self.responseDict = json.loads(self.data.decode())
		#print (json.dumps(responseDict, sort_keys=True, indent=2))
		return self.responseDict

	def players(self):
		self.data = {
				"id": 1, 
				"method": "slim.request", 
				"params": [
					"", 
					[
						"serverstatus" ,
						"0", 
						"999"
					]
				]
			}
		
		self.responseDict = self.sendRequest(self.data)
		self.numberOfPlayers = self.responseDict['result']["player count"]
		#print ("Players Found: %s" % numberOfPlayers)

		self.players = self.responseDict['result']["players_loop"]
		#print ("Player list: %s" % json.dumps(players, sort_keys=True, indent=2))
		
		return self.players
		
	def power(self, player, command):
		self.player = player
		self.command = command
		
		self.data = {
				"id":1,
				"method":"slim.request",
				"params":[
					self.player,
					[
						"power",
						self.powerCommand[self.command]
					]
				]
			}
		
		self.responseDict = self.sendRequest(self.data)
		try:
			self.powerStatus = self.responseDict['result']["_power"]
			print ("Power: %s" % self.powerStatus)
			#return self.powerCommand[self.powerStatus]
		except KeyError, e:
			return None
		
	def playlist(self, player, command):
		self.player = player
		self.command = command
		
		self.data = {
				"id":1,
				"method":"slim.request",
				"params":[
					self.player,
					[
						self.command
					]
				]
			}
		
		self.responseDict = self.sendRequest(self.data)
		
		
		
		