import pygame
from gameEngine import getDist
from PodSixNet.Channel import Channel

#-----------------------------------------------------------------------
# ClientChannel : connection to the client
#-----------------------------------------------------------------------

class ClientChannel(Channel):
	"""
	This is the server representation of a single connected client.
	"""
	def __init__(self, *args, **kwargs):
		#print "Init client channel : %s // %s" % (args, kwargs)
		#self.nickname = "anonymous"
		self.id = "none"
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		self._server.DelPlayerChannel(self)
		self._server.delPlayer(self.id)
	
	#-------------------------------------------------------------------
	# on server receive from client self.id :
	#-------------------------------------------------------------------
	
	#-------------------------------------------------------------------
	# login
	
	def Network_nickname(self, data):
		self.id = data["id"]
		if self.id in self._server.players:
			print "Player %s already connected" % (self.id)
			self.Close()
			return
		
		self._server.players[self.id] = self
		self._server.addPlayer("start", self.id, 50, 70)
		print "player %s logged in." % (self.id)
		self._server.SendMapPlayers("start")
		#if "none" in self._server.players:
		#	del self._server.players["none"]
		
	def Network_login(self, data):
		self.id = data['id']
		self.password = data['password']
		if self._server.db.checkLogin(self.id, self.password):
			if self.id in self._server.players:
				print "Error, %s is already connected"
				return False
				
			self._server.players[self.id] = self
			self._server.addPlayer("start", self.id, 50, 70)
			print "player %s logged in." % (self.id)
			self._server.SendPlayers()
			if "none" in self._server.players:
				del self._server.players["none"]
	
	#-------------------------------------------------------------------
	# info request
	def Network_warp_info_request(self, data={}):
		self._server.SendWarpInfo(self.id)
	
	#-------------------------------------------------------------------
	# movements
	
	def Network_player_update_move(self, data):
		#print "Pos msg to send to client : %s" % (data)
		id = self.id
		mapName = self._server.playerMaps[id]
		x = data['x']
		y = data['y']
		dx = data['dx']
		dy = data['dy']
		
		self._server.SendPlayerUpdateMove(mapName, id, x, y, dx, dy)
		#self._server.SendToAll({"action": "player_update_move", "id": self.id, "x":data['x'], "y":data['y'], "dx":data['dx'], "dy":data['dy']})
		playerMapRect = self._server.maps[mapName].players[self.id].mapRect
		d= getDist(playerMapRect, pygame.Rect((x, y,0,0)))
		print "Network player update: x", x, 'y', y, 'd', d
		if d>20.0:
			print("Warning : %s says he's at %s pixels from where i know he should be. I'll warp that sucker!" % (self.id, d))
			playerx = playerMapRect.x
			playery = playerMapRect.y
			self._server.warpPlayer(id, mapName, playerx,playery)
		else:
			self._server.maps[mapName].players[self.id].setPos(x, y)
		self._server.maps[mapName].players[self.id].setMovement(dx, dy)
	
	def Network_warp_request(self, data):
		id = self.id
		self._server.warpPlayer(id, "second", 50,70)
		
	#-------------------------------------------------------------------
	# attack
	
	def Network_attack_mob(self, data):
		target = data['target']
		self._server.onPlayerAttackMob(self.id, target)
	
	#-------------------------------------------------------------------
	# chat
	def Network_public_message(self, data):
		mapName = self._server.playerMaps[self.id]
		self._server.SendToMap(mapName, {"action": "public_message", "message": data['message'], "id": self.id})
		#self._server.SendToAll({"action": "public_message", "message": data['message'], "id": self.id})
		
	def Network_private_message(self, data):
		if data["target"] in self._server.players:
			self._server.SendTo(data["target"], {"action": "private_message", "message": data['message'], "id": self.id})
		else:
			msg = "%s not connected" % (data["target"])
			self._server.SendTo(self.id, {"action": "private_message", "message": msg, "id": 'server'})
	
	def Network_emote(self, data):
		emote = data['emote']
		self._server.SendToMap(self._server.playerMaps[self.id], {"action": "emote", "id": self.id, "emote" : emote})
