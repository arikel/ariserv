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

from dbHandler import dbHandler
from gameEngine import *

from clientChannel import ClientChannel

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
	
	def SendWarpInfo(self, playerName):
		mapName = self.playerMaps[playerName]
		for warp in self.maps[mapName].warps:
			name = warp.name
			x = warp.x
			y = warp.y
			w = warp.w
			h = warp.h
			self.SendTo(playerName, {'action':'warp_info', 'name':name, 'x':x, 'y':y, 'w':w, 'h':h})
	
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
		
		
	def onPlayerAttackMob(self, playerId, mobId):
		if playerId not in self.playerMaps:
			return
		mapName = self.playerMaps[playerId]
		if mobId not in self.maps[mapName].mobs:
			return
		mob = self.maps[mapName].mobs[mobId]
		dist = getDist(mob.mapRect, self.maps[mapName].players[playerId].mapRect)
		if dist > 40.0:
			return
		dmg = random.randint(1,6)
		self.SendMobTookDamage(mapName, mobId, dmg)
		mob.takeDamage(dmg)
		mob.setMovement(0,0)
		self.SendMobUpdateMove(mapName, mobId, mob.x, mob.y, 0,0)
		if mob.hp <= 0:
			self.onMobDie(mapName, mobId)
		
	def onMobDie(self, mapName, mobId):
		if mobId not in self.maps[mapName].mobs:
			return
		self.maps[mapName].delMob(mobId)
		self.SendMobLeaveMap(mapName, mobId)
		self.maps[mapName].addMob(1, 80,80)
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
