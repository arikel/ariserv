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
#import random

from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

from functions import ustr, getDist

from dbHandler import dbHandler
from gameEngine import *


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
		if d>16.0:
			print("Warning : %s says he's at %s pixels from where i know he should be. I'll warp that sucker!" % (self.id, d))
			playerx = playerMapRect.x
			playery = playerMapRect.y
			self._server.warpPlayer(id, mapName, playerx,playery)
		#else:
		#	self._server.maps[mapName].players[self.id].setPos(x, y)
		self._server.maps[mapName].players[self.id].setMovement(dx, dy)
	
	def Network_warp_request(self, data):
		id = self.id
		self._server.warpPlayer(id, "second", 50,70)
		
	#-------------------------------------------------------------------
	# attack
	
	def Network_attack_mob(self, data):
		target = data['target']
		self._server.OnPlayerAttackMob(self.id, target)
	
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



#-----------------------------------------------------------------------
# GameServer
#-----------------------------------------------------------------------
class GameServer(Server):
	channelClass = ClientChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.playerChannels = {}#WeakKeyDictionary() # playerChannel -> True
		self.players = {} # playerId -> playerChannel
		self.playerMaps = {} # playerId -> mapName
		
		self.db = dbHandler("save/essai.db")
		
		self.maps = {}
		self.addMap("data/start.txt")
		self.addMap("data/second.txt")
		
		print 'Server launched'
		
		for m in self.maps:
			for i in range(15):
				self.maps[m].addMob(1,50.0,50.0)
		
		
		self.prevTime = 0.0
		
		pygame.init()
		
	#-------------------------------------------------------------------
	# generic purpose server to client
	#-------------------------------------------------------------------
	
	def SendTo(self, playerName, data):
		self.players[playerName].Send(data)
	
	def SendToAll(self, data):
		[p.Send(data) for p in self.playerChannels]
	
	def SendToMap(self, mapName, data):
		for playerName in self.maps[mapName].players:
			self.SendTo(playerName, data)
	
	def Launch(self):
		while True:
			t = pygame.time.get_ticks()
			dt = t - self.prevTime
			self.prevTime = t
			
			if dt:
				#print "Server Main Loop : t = %s, dt = %s" % (t, dt)
				for m in self.maps:
					self.maps[m].update(dt)
			
			self.Pump()
			sleep(0.0001)
	
	
	
	def Connected(self, channel, addr):
		self.AddPlayerChannel(channel)
	
	def AddPlayerChannel(self, playerChannel):
		print "New player connected from " + str(playerChannel.addr) + ", waiting to log in..."
		self.playerChannels[playerChannel] = True
		
	def DelPlayerChannel(self, playerChannel):
		print "Deleting Player connection for " + str(playerChannel.addr)
		del self.playerChannels[playerChannel]
		#self.SendPlayers()
		
	#-------------------------------------------------------------------
	# server messages to client
	#-------------------------------------------------------------------
	def SendPlayers(self):
		for mapName in self.maps:
			self.SendMapPlayers(mapName)
			
	def SendMapPlayers(self, mapName):
		mapPlayers = self.maps[mapName].players.keys()
		for playerName in mapPlayers:
			player = self.maps[mapName].players[playerName]
			self.SendPlayerUpdateMove(mapName, playerName, player.x, player.y, player.dx, player.dy)
	
	def SendWarpInfo(self, playerId):
		mapName = self.playerMaps[playerId]
		for warp in self.maps[mapName].warps:
			name = warp.name
			x = warp.x
			y = warp.y
			w = warp.w
			h = warp.h
			self.SendTo(playerId, {'action':'warp_info', 'name':name, 'x':x, 'y':y, 'w':w, 'h':h})
	
	def SendPlayerUpdateMove(self, mapName, playerName, x, y, dx, dy):
		self.SendToMap(mapName, {"action": "player_update_move", "id": playerName, "x" : x, "y" : y, "dx" : dx, "dy" : dy})
	
	def SendMobUpdateMove(self, mapName, mobId, x, y, dx, dy):
		self.SendToMap(mapName, {"action": "mob_update_move", "id": mobId, "x" : x, "y" : y, "dx" : dx, "dy" : dy})
	
	def SendPlayerEnterMap(self, mapName, playerName):
		player = self.maps[mapName].players[playerName]
		x = player.x
		y = player.y
		dx = player.dx
		dy = player.dy
		self.SendToMap(mapName, {"action": "player_enter_map", "id": playerName, "x":x, "y":y, "dx":dx, "dy":dy})
	
	def SendPlayerLeaveMap(self, mapName, playerName):
		self.SendToMap(mapName, {"action": "player_leave_map", "id": playerName})
	
	def SendPlayerWarp(self, mapName, playerName, x, y):
		mapFileName = self.maps[mapName].filename
		self.SendTo(playerName, {"action": "warp", "mapFileName" : mapFileName, "x":x, "y":y})	
	
	def SendMobLeaveMap(self, mapName, mobId):
		self.SendToMap(mapName, {"action": "mob_leave_map", "id": mobId})
	
	def SendMobTookDamage(self, mapName, mobId, dmg):
		self.SendToMap(mapName, {"action": "mob_took_damage", "id": mobId, "dmg":dmg})
	
	def addMap(self, filePath):
		m = GameMap(self, filePath)
		self.maps[m.name] = m
		print "Map '%s' added to server" % (m.name)
		
	
	
	def addPlayer(self, mapName, playerName, x, y):
		self.playerMaps[playerName] = mapName
		self.maps[mapName].addPlayer(playerName, x, y)
		self.SendPlayerEnterMap(mapName, playerName)
		
	def delPlayer(self, playerName):
		if playerName in self.playerMaps:
			mapName = self.playerMaps[playerName]
			self.maps[mapName].delPlayer(playerName)
			self.SendPlayerLeaveMap(mapName, playerName)
			del self.players[playerName]
			del self.playerMaps[playerName]
	
	def warpPlayer(self, playerName, newMapName, x, y):
		mapName = self.playerMaps[playerName]
		if mapName == newMapName:
			player = self.maps[mapName].players[playerName]
			player.setPos(x, y)
			self.SendPlayerUpdateMove(mapName, playerName, x, y, 0, 0)
			return
		
		self.maps[mapName].delPlayer(playerName)
		self.SendPlayerLeaveMap(mapName, playerName)
		
		self.maps[newMapName].addPlayer(playerName, x, y)
		self.SendPlayerWarp(newMapName, playerName, x, y)
		self.SendPlayerEnterMap(newMapName, playerName)
		self.playerMaps[playerName] = newMapName
		#print("warped player %s from map %s to map %s : %s / %s" % (playerName, mapName, newMapName, x, y))
		
	def addMob(self, mapName, mobId, x=60,y=60):
		self.maps[mapName].addMob(mobId, x, y)
		
		
	def OnPlayerAttackMob(self, playerId, mobId):
		if playerId not in self.playerMaps:
			return
		mapName = self.playerMaps[playerId]
		if mobId not in self.maps[mapName].mobs:
			return
		dist = getDist(self.maps[mapName].mobs[mobId].mapRect, self.maps[mapName].players[playerId].mapRect)
		if dist > 35.0:
			return
		self.maps[mapName].delMob(mobId)
		self.SendMobTookDamage(mapName, mobId, random.randint(1,6))
		self.SendMobLeaveMap(mapName, mobId)
		
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
	s = GameServer(localaddr=("88.173.217.230", 18647), listeners=5000)
	s.Launch()
