import pygame
from PodSixNet.Channel import Channel
from gameEngine import getDist
from dbHandler import isValidName, isValidPassword
#-----------------------------------------------------------------------
# ClientChannel : connection to the client
#-----------------------------------------------------------------------

class ClientChannel(Channel):
	"""
	This is the server representation of a single connected client.
	"""
	def __init__(self, *args, **kwargs):
		#print "Init client channel : %s // %s" % (args, kwargs)
		self.name = "none"
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		self._server.DelPlayerChannel(self)
		self._server.delPlayer(self.name)
	
	#-------------------------------------------------------------------
	# on server receive from client self.name :
	#-------------------------------------------------------------------
	
	#-------------------------------------------------------------------
	# login
	
	def Network_nickname(self, data):
		self.name = data["id"]
		if self.name in self._server.players:
			msg = "Player %s already connected" % (self.name)
			self._server.log(msg)
			self.Close()
			return
		
		self._server.players[self.name] = self
		self._server.addPlayer("start", self.name, 50, 70)
		msg = "player %s logged in." % (self.name)
		self._server.log(msg)
		
		self._server.SendMapPlayers("start")
		#if "none" in self._server.players:
		#	del self._server.players["none"]
		
	def Network_login(self, data):
		self.name = data['id']
		self.password = data['password']
		msg = "received login for %s, pass = %s" % (data["id"], data["password"])
		self._server.log(msg)
		
		# check login / password
		if self._server.db.checkLogin(self.name, self.password):
			if self.name in self._server.players:
				msg = "Error, %s is already connected"
				self._server.log(msg)
				return False
			
			# LOGIN accepted
			self._server.SendLoginAccepted(self)
			self._server.players[self.name] = self
			self._server.addPlayer("start", self.name, 50, 70)
			msg = "player %s logged in." % (self.name)
			self._server.log(msg)
			
			#self._server.SendPlayers()
			if "none" in self._server.players:
				del self._server.players["none"]
		# LOGIN error
		else:
			if self._server.db.getPlayer(self.name):
				msg = "I know player %s, but password %s doesn't match" % (self.name, self.password)
				self._server.log(msg)
				self._server.SendLoginError(self, "wrong password")
				
			else:
				msg = "Player %s unknown" % (self.name)
				self._server.log(msg)
				self._server.SendLoginError(self, "player unknown")
		
	def Network_register(self, data):
		self.name = data['id']
		self.password = data['password']
		msg = "received register for %s, pass = %s" % (data["id"], data["password"])
		self._server.log(msg)
		
		if self._server.db.hasPlayer(self.name):
			msg = "Player %s already exists" % (self.name)
			self._server.log(msg)
			self._server.SendRegisterError(self, msg)
			return
		if not isValidName(self.name):
			msg = "%s is not a valid name, keep it simple." % (self.name)
			self._server.log(msg)
			self._server.SendRegisterError(self, msg)
			return
			
		if not isValidPassword(self.password):
			msg = "%s is not a valid password, more than 4 characters please." % (self.password)
			self._server.log(msg)
			self._server.SendRegisterError(self, msg)
			return
			
		self._server.db.addPlayer(self.name, self.password)
		msg = "Registered player %s" % (self.name)
		self._server.log(msg)
		msg = "The player %s has been registered, you may now login." % (self.name)
		self._server.SendRegisterAccepted(self, msg)
	#-------------------------------------------------------------------
	# info request
	def Network_warp_info_request(self, data={}):
		self._server.SendWarpInfo(self.name)
	
	#-------------------------------------------------------------------
	# movements
	
	def Network_player_update_move(self, data):
		#print "Pos msg to send to client : %s" % (data)
		name = self.name
		mapName = self._server.playerMaps[name]
		x = data['x']
		y = data['y']
		dx = data['dx']
		dy = data['dy']
		
		self._server.SendPlayerUpdateMove(mapName, name, x, y, dx, dy)
		#self._server.SendToAll({"action": "player_update_move", "id": self.id, "x":data['x'], "y":data['y'], "dx":data['dx'], "dy":data['dy']})
		playerMapRect = self._server.maps[mapName].players[self.name].mapRect
		d= getDist(playerMapRect, pygame.Rect((x, y,0,0)))
		#print "Network player update: x", x, 'y', y, 'd', d
		if d>20.0:
			msg = "Warning : %s says he's at %s pixels from where i know he should be. I'll warp that sucker!" % (self.name, d)
			self._server.log(msg)
			playerx = playerMapRect.x
			playery = playerMapRect.y
			self._server.warpPlayer(name, mapName, playerx,playery)
		else:
			self._server.maps[mapName].players[self.name].setPos(x, y)
		
		self._server.maps[mapName].players[self.name].setMovement(dx, dy)
	
	def Network_warp_request(self, data):
		name = self.name
		self._server.warpPlayer(name, "second", 50,70)
		
	#-------------------------------------------------------------------
	# attack
	
	def Network_attack_mob(self, data):
		target = data['target']
		self._server.onPlayerAttackMob(self.name, target)
	
	#-------------------------------------------------------------------
	# chat
	def Network_public_message(self, data):
		mapName = self._server.playerMaps[self.name]
		self._server.SendToMap(mapName, {"action": "public_message", "message": data['message'], "id": self.name})
		
		
	def Network_private_message(self, data):
		if data["target"] in self._server.players:
			self._server.SendTo(data["target"], {"action": "private_message", "message": data['message'], "id": self.name})
		else:
			msg = "%s not connected" % (data["target"])
			self._server.SendTo(self.name, {"action": "private_message", "message": msg, "id": 'server'})
	
	def Network_emote(self, data):
		emote = data['emote']
		self._server.SendToMap(self._server.playerMaps[self.name], {"action": "emote", "id": self.name, "emote" : emote})
