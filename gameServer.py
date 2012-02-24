#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
from time import sleep
#from weakref import WeakKeyDictionary
try:
	import psyco
	psyco.full()
except:
	pass

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

from functions import ustr, getDist

from dbHandler import dbHandler
from gameEngine import *

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
		self._server.DelPlayer(self)
	
	##################################
	### Network specific callbacks ###
	##################################
	#-------------------------------------------------------------------
	# on server receive from client self.nickname :
	#-------------------------------------------------------------------
	
	#-------------------------------------------------------------------
	# login
	
	def Network_nickname(self, data):
		#self.nickname = data['nickname']
		#self.name = data['nickname']
		#if self.name != "anonymous":
		self.id = data["id"]
		
		self._server.players[self.id] = self
		self._server.map.addPlayer(Player(self.id, self._server.map, 50, 70))
		print "player %s logged in." % (self.id)
		self._server.SendPlayers()
		#if "none" in self._server.players:
		#	del self._server.players["none"]
		
	def Network_login(self, data):
		self.id = data['id']
		self.password = data['password']
		if self._server.db.checkLogin(self.id, self.password):
			self._server.players[self.id] = self
			self._server.SendPlayers()
			if "none" in self._server.players:
				del self._server.players["none"]
	
	#-------------------------------------------------------------------
	# movements
		
	def Network_update_move(self, data):
		#print "Pos msg to send to client : %s" % (data)
		x = data['x']
		y = data['y']
		dx = data['dx']
		dy = data['dy']
		
		self._server.SendToAll({"action": "update_move", "who": self.id, "x":data['x'], "y":data['y'], "dx":data['dx'], "dy":data['dy']})
		
		self._server.map.players[self.id].setPos(x, y)
		self._server.map.players[self.id].setMovement(dx, dy)
	
	#-------------------------------------------------------------------
	# chat
	def Network_public_message(self, data):
		self._server.SendToAll({"action": "public_message", "message": data['message'], "who": self.id})
		
	def Network_private_message(self, data):
		if data["target"] in self._server.players:
			self._server.SendTo(data["target"], {"action": "private_message", "message": data['message'], "who": self.id})
		else:
			msg = "%s not connected" % (data["target"])
			self._server.SendTo(self.id, {"action": "private_message", "message": msg, "who": 'server'})
	
	def Network_emote(self, data):
		id = data['id']
		emote = data['emote']
		self._server.SendToAll({"action": "emote", "id": self.id, "emote" : emote})
		
class GameServer(Server):
	channelClass = ClientChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.playerChannels = {}#WeakKeyDictionary() # playerChannel -> True
		self.players = {} # playerId -> playerChannel
		
		self.mobs = {} # id -> Mob
		
		self.db = dbHandler("db/essai.db")
		
		#self.map = MapBase("maps/001-1.tmx")
		self.map = GameMap("maps/testmap.txt")
		
		print 'Server launched'
		
		for i in range(15):
			name = "mob_" + str(i)
			self.addMob(name, 50,60)
			self.mobs[name].setMovement(0,0)
		
		self.prevTime = 0.0
		self.nextMobUpdateTime = 0.0
		pygame.init()
		
	def Connected(self, channel, addr):
		self.AddPlayer(channel)
	
	def AddPlayer(self, playerChannel):
		print "New anon player" + str(playerChannel.addr) + " name : " + playerChannel.id
		self.playerChannels[playerChannel] = True
		
		#self.SendPlayers()
		print "players", [p for p in self.playerChannels]
		
	def addMob(self, id, x=50,y=50):
		mob = Mob(id, 1, self.map, x, y)
		self.mobs[id] = mob
		self.map.addMob(mob, x=60, y=60)
		
	def DelPlayer(self, playerChannel):
		print "Deleting Player" + str(playerChannel.addr)
		del self.playerChannels[playerChannel]
		self.SendPlayers()
	
	#-------------------------------------------------------------------
	# generic purpose server to client
	#-------------------------------------------------------------------
	
	def SendTo(self, playerName, data):
		self.players[playerName].Send(data)
	
	def SendToAll(self, data):
		[p.Send(data) for p in self.playerChannels]
	
	#def SendToList(self, playerList, data):# list of players names to send to
	#	[self.players[p].Send(data) for p in self.playerList]
	
	def Launch(self):
		while True:
			t = pygame.time.get_ticks()
			dt = t - self.prevTime
			self.prevTime = t
			
			#print "Server Main Loop : t = %s, dt = %s" % (t, dt)
			self.map.update(dt)
			
			if t>self.nextMobUpdateTime:
				self.nextMobUpdateTime = t + 200
				for mob in self.mobs.values():
					data = {'action' : 'mob_update_move', 'x':mob.x, 'y':mob.y, 'dx':mob.dx, 'dy':mob.dy, 'id':mob.id}
					self.SendToAll(data)
			self.Pump()
			sleep(0.0001)
	
	#-------------------------------------------------------------------
	# server send to client
	#-------------------------------------------------------------------
	def SendPlayers(self):
		
		self.SendToAll({"action": "players", "players": [p.id for p in self.playerChannels], "who": "server"})
		for p in self.playerChannels:
			if p.id in self.map.players:
				player = self.map.players[p.id]
				self.SendToAll({"action": "update_move", "who": p.id, "x":player.x, "y":player.y, "dx":player.dx, "dy":player.dy})
				#print "player in list known : %s is at %s %s" % (p.id, player.x, player.y)
			else:
				print "warning : %s not in map" % (p.id)
	
	def SendMobUpdateMove(self, mobId=1):
		self.SendToAll({"action": "mob_update_move", "who": "server", "id":mobId, "x" : self.mobs[mobId].x, "y" : self.mobs[mobId].y, "dy" : self.mobs[mobId].dy})
	
	def SendMobs(self):
		self.SendToAll({"action": "mobs", "mobs": [p.id for p in self.mobs], "who": "server"})
	
	
'''
# get command line argument of server, port
if len(sys.argv) != 2:
	print "Usage:", sys.argv[0], "host:port"
	print "e.g.", sys.argv[0], "localhost:31425"
else:
	host, port = sys.argv[1].split(":")
	s = GameServer(localaddr=(host, int(port)))
	s.Launch()
'''

if __name__=="__main__":
	s = GameServer(localaddr=("88.173.217.230", 18647))
	s.Launch()
