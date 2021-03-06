#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import time
#from time import sleep
#from weakref import WeakKeyDictionary
try:
	import psyco
	psyco.full()
except:
	pass

import pygame
import random

from PodSixNet.Server import Server

from dbHandler import DbHandler, isValidName, isValidPassword
#from gameEngine import *
from gameEngine import Player, Mob, GameMap, getDist

from clientChannel import ClientChannel

#-----------------------------------------------------------------------
# Logger
#-----------------------------------------------------------------------
class Logger(object):
	def __init__(self, filename = "log.txt"):
		self.filename = filename
		
	def write(self, msg):
		self.logfile = open(self.filename, 'a')
		today = time.strftime("%Y%m%d%H%M")
		print "(log) %s %s" % (today, msg)
		
		msg = today + " : " + msg + "\n"
		
		self.logfile.write(msg)
		self.logfile.close()
		
	def quit(self):
		self.logfile.close()

#-----------------------------------------------------------------------
# GameServer
#-----------------------------------------------------------------------
class GameServer(Server):
	channelClass = ClientChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.playerChannels = {}#WeakKeyDictionary() # playerChannel -> True
		self.players = {} # playerName -> playerChannel
		self.playerMaps = {} # playerName -> mapName
		
		self.db = DbHandler("save/essai.db")
		self.logger = Logger()
		
		self.maps = {}
		self.addMap("data/start.txt")
		self.addMap("data/second.txt")
		
		self.log('Server launched')
		
		for m in self.maps:
			for i in range(15):
				self.maps[m].addMob(1,50.0,50.0)
		
		self.prevTime = 0.0
		pygame.init()
		
	def log(self, msg):
		self.logger.write(msg)
		
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
			time.sleep(0.0001)
	
	
	
	def Connected(self, channel, addr):
		self.AddPlayerChannel(channel)
	
	def AddPlayerChannel(self, playerChannel):
		msg = "New player connected from " + str(playerChannel.addr) + ", waiting to log in..."
		self.log(msg)
		self.playerChannels[playerChannel] = True
		
	def DelPlayerChannel(self, playerChannel):
		msg = "Deleting Player connection for " + str(playerChannel.addr)
		self.log(msg)
		del self.playerChannels[playerChannel]
		#self.SendPlayers()
		
	#-------------------------------------------------------------------
	# server messages to client
	#-------------------------------------------------------------------
	def SendLoginError(self, playerChannel, msg):
		if playerChannel not in self.playerChannels:
			self.log("Login Error : player channel unknown")
			return
		data = {"action":"login_error", "msg" : msg}
		playerChannel.Send(data)
		
	def SendLoginAccepted(self, playerChannel):
		if playerChannel not in self.playerChannels:
			self.log("Login Error : player channel unknown")
			return
		msg = "Sending login accepted"
		self.log(msg)
		
		data = {"action":"login_accepted", "mapFileName" : "maps/testmap.txt", "x": 50, "y":50}
		playerChannel.Send(data)
		
	def SendRegisterError(self, playerChannel, msg):
		if playerChannel not in self.playerChannels:
			self.log("Register Error : player channel unknown")
			return
		data = {"action":"register_error", "msg" : msg}
		playerChannel.Send(data)
		
	def SendRegisterAccepted(self, playerChannel, msg):
		if playerChannel not in self.playerChannels:
			self.log("Register Error : player channel unknown")
			return
		data = {"action":"register_accepted", "msg" : msg}
		playerChannel.Send(data)
		
		
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
		mapFileName = self.maps[mapName].mapFilename
		self.SendTo(playerName, {"action": "warp", "mapFileName" : mapFileName, "x":x, "y":y})	
		
	def SendMobLeaveMap(self, mapName, mobId):
		self.SendToMap(mapName, {"action": "mob_leave_map", "id": mobId})
	
	def SendMobTookDamage(self, mapName, mobId, dmg):
		self.SendToMap(mapName, {"action": "mob_took_damage", "id": mobId, "dmg":dmg})
	
	def addMap(self, filePath):
		m = GameMap(self, filePath)
		self.maps[m.name] = m
		#print "Map '%s' added to server" % (m.name)
		
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
			#self.SendPlayerUpdateMove(mapName, playerName, x, y, 0, 0)
			self.SendPlayerWarp(newMapName, playerName, x, y)
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
