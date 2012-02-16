#!/usr/bin/python
# -*- coding: utf8 -*-
from tmxHandler import *

class Item:
	weight = 0.1
	baseCost = 2
	baseSold = 1
	itemId = 0
	def __init__(self, itemId):
		self.itemId = itemId
		
		
class Inventory:
	
	def __init__(self):
		self.clear()
		
	def clear(self):
		self.items = {}
		
	def addItem(self, itemId, number):
		if itemId in self.items:
			self.items[itemId] += int(number)
		else:
			self.items[itemId] = int(number)
	
	def get(self):
		keys = self.items.keys()
		keys.sort()
		res = ""
		for key in keys:
			res = res + str(key) + "," + str(self.items[key]) + ";"
		return res
		
	def set(self, itemString):
		self.items = {}
		itemString = itemString.strip()
		for elem in split(itemString, ';'):
			item = elem.split(',')
			if len(item)==2:
				self.addItem(item[0].strip(), item[1].strip())

class MapObject:
	_map = None
	def __init__(self, id, _map = None):
		self.id = id
		self._map = _map
		
		# float pixel position on map
		self.category = None
		self.currentMapName = None
		self._map = None
		self.x = 0.0
		self.y = 0.0
		self.mapRect = pygame.Rect(0,0,1,1)
		
		# movement
		self.dx = 0.0
		self.dy = 0.0
		self.speed = 0.2
		self.mobile = False
		
		self.currentAnim = "idle"
		self.state = "idle"
		self.target = None
		self.timer = 0.0
		self.path = [] # [(x, y), (x2, y2)...]
		
	def setPos(self, x, y):
		self.x = x
		self.y = y
		self.mapRect.topleft = (x,y)
	
	def getPos(self):
		return (self.x, self.y)
	
	def move(self, x, y):
		self.setPos(self.x + x, self.y + y)
	
	def setMovement(self, x, y):
		self.dx = x # -1, 0, 1
		self.dy = y

	def update(self, dt=0.0):
		if self.mobile:
			self.move(self.dx*dt, self.dy*dt)
	
	def nextMovePossible(dt=0.0):
		if not self._map:
			return False
		if self._map.collidePos(self.x + self.dx*dt, self.y + self.dy*dt):
			return False
		return True

class Being(object):
	def __init__(self, id):
		self.id = id
		
		self.hp = 1
		self.hpMax = 1
		
		self.carac = {}
		for carac in ["str", "dex", "cons", "wil"]:
			self.carac[carac] = 1
		
		self.skills = {}
		
	def heal(self, n):
		self.hp += n
		# keep hp between 0 and hpMax
		self.hp = min(max(self.hp, 0), self.maxHp)
		
	def getCarac(self, caracName):
		if caracName in self.carac:
			return self.carac[caracName]
		return 0
		
	def getSkill(self, skillName):
		if skillName in self.skills:
			return self.skills[skillName]
		return 0
		
	
class Mob(Being, MapObject):
	def __init__(self, id, mobId, _map, x, y):
		Being.__init__(self, id)
		MapObject.__init__(self, id, _map)
		self.mobile = True
		self.category = "mob"
		self.mobId = mobId
		
		self.setPos(x, y)
		
		
class Player(Being, MapObject):
	def __init__(self, id, _map, x, y):
		Being.__init__(self, id)
		MapObject.__init__(self, id, _map)
		self.mobile = True
		self.category = "player"
		self.setPos(x, y)
		
		
class MapBase:
	def __init__(self, filename=None):
		self.filename = filename
		if self.filename:
			self.load(self.filename)
		
		self.mapObjects = []
		self.mobs = []
		self.players = []
		self.npcs = []
		
	def load(self, filename):	
		self.mapData = TmxMapData()
		self.mapData.load(self.filename)
		
		self.width = self.mapData.width
		self.height = self.mapData.height
		
		self.tileWidth = self.mapData.tileWidth
		self.tileHeight = self.mapData.tileHeight
		
		self.collisionLayer = TileLayer("collisionLayer",
			self.width,
			self.height,
			decode(self.mapData.getLayerData("collision"))
		)
		
		self.collisionGrid = TileLayer("collisionGrid",
			self.width,
			self.height,
			decode(self.mapData.getLayerData("collision"))
		)
		
	def tileCollide(self, x, y): # tile position collide test
		if self.collisionGrid.tiles[x][y]>0:
			#print "%s / %s collides" % (x,y)
			return True
		return False
		
	def posCollide(self, x, y): # pixel position collide test
		return self.tileCollide(int(x)/self.tileWidth, int(y)/self.tileHeight)
		
	def blockTile(self, x, y):
		self.collisionGrid.tiles[x][y] = 1
		
	def freeTile(self, x, y):
		self.collisionGrid.tiles[x][y] = 0
	
	def revertTile(self, x, y):
		self.collisionGrid.tiles[x][y] = self.collisionLayer.tiles[x][y]
	
		
	def addPlayer(self, player, x=None, y=None):
		if x == None:
			x = player.x
			y = player.y
		if player.id not in self.players:
			self.players[player.id]=player
			player._map = self
			self.players[player.id].setPos(x, y)
			
	def delPlayer(self, playerName):
		del self.players[playerName]
		
	def update(self, dt):
		for player in self.players.values():
			player.update(dt)
			#print "updated pos for player %s : %s / %s, direction : %s / %s" % (player.id, player.x, player.y, player.dx, player.dy)
			
	
