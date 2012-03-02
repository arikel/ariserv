#!/usr/bin/python
# -*- coding: utf8 -*-
from tmxHandler import *
import random
import math

def getDist(a, b):# a, b == Rect or derivative : Player, Mob...
	return math.sqrt((a.x-b.x)**2+(a.y-b.y)**2)
	
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
	def __init__(self, id, _map = None):
		self.id = id
		self._map = _map
		
		self.category = None
		self.currentMapName = None
		# float pixel position on map
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
		if not self.mobile:
			return
		if self.nextMovePossible(dt):
			self.move(self.speed*self.dx*dt, self.speed*self.dy*dt)
			return
		
		# in case of collision, handle possible sliding
		oldDx = self.dx
		oldDy = self.dy
		
		self.setMovement(0, self.dy)
		if self.nextMovePossible(dt):
			self.move(self.speed*self.dx*dt, self.speed*self.dy*dt)
		else:
			self.setMovement(oldDx, 0)
			if self.nextMovePossible(dt):
				self.move(self.speed*self.dx*dt, self.speed*self.dy*dt)
		
	def nextMovePossible(self, dt=0.0):
		if not self._map:
			print "player has no map"
			return False
		if self._map.posCollide(self.x + self.dx*self.speed*dt, self.y + self.dy*self.speed*dt):
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
		self.timer = 0
		self.state = "idle"
		self.speed = 0.05
		
	def update(self, dt=0.0):
		self.timer += dt
		if not self.mobile:
			return
		if self.nextMovePossible(dt):
			self.move(self.speed*self.dx*dt, self.speed*self.dy*dt)
		else:
			self.setMovement(0,0)
			self._map.sendMobUpdateMove(self.id)
		#print "--- mob %s updating movement :"
		if self.timer > 5000:
			self.timer = 0
			if random.randint(1,2)>1:
				self.dx = 0
				self.dy = 0
				self._map.sendMobUpdateMove(self.id)
				return False
			
			self.dx = random.randint(1,3) -2
			self.dy = random.randint(1,3) -2
			self._map.sendMobUpdateMove(self.id)
			#print "mob %s changing movement %s / %s" % (self.id, self.dx, self.dy)
			return True
		
		
		
		return False
		
class Player(Being, MapObject):
	def __init__(self, id, _map, x, y):
		Being.__init__(self, id)
		MapObject.__init__(self, id, _map)
		self.mobile = True
		self.category = "player"
		self.setPos(x, y)
		
'''	
class MapBase:
	def __init__(self, filename=None):
		self.filename = filename
		if self.filename:
			self.load(self.filename)
		
		self.mobs = {}
		self.players = {}
		
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
		if not (0<=x<len(self.collisionGrid.tiles)):
			return True
		if not (0<=y<len(self.collisionGrid.tiles[0])):
			return True
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
	
	def addMob(self, mob, x=None, y=None):
		if x == None:
			x = mob.x
			y = mob.y
		if mob.id not in self.mobs:
			print "Engine : adding mob : %s -> %s" % (mob.id, mob)
			self.mobs[mob.id]=mob
			mob._map = self
			self.mobs[mob.id].setPos(x, y)
	
	def delMob(self, mobId):
		del self.mobs[mobId]
		
	def update(self, dt):
		for player in self.players.values():
			player.update(dt)
			#print "updated player %s : %s / %s" % (player.id, player.x, player.y)
			
		for mob in self.mobs.values():
			mob.update(dt)
			#print "updating mob %s : %s / %s, dt = %d" % (mob.id, mob.x, mob.y, dt)
			#print "updated pos for player %s : %s / %s, direction : %s / %s" % (player.id, player.x, player.y, player.dx, player.dy)
'''			

class MapLayer(object):
	def __init__(self, name, w, h, tileWidth=16, tileHeight=16):
		self.name = name
		self.w = w # width in tiles
		self.h = h # height in tiles
		self.tileWidth = tileWidth
		self.tileHeight = tileHeight
		
		self.tiles = [] # [x][y] : code
		for x in range(self.w):
			line = []
			for y in range(self.h):
				line.append("0000")
			self.tiles.append(line)
		
	def isValidPos(self, x, y):
		if (0<=x<self.w) and (0<=y<self.h):
			return True
		return False
		
	def getTile(self, x, y):
		return self.tiles[x][y]
		
	def setTile(self, x, y, code):
		self.tiles[x][y] = code
		
	def clearTile(self, x, y):
		if self.name == "collision":
			self.tiles[x][y] = 0
		else:
			self.tiles[x][y] = "0000"
		
	def fill(self, code):
		for x in range(self.w):
			for y in range(self.h):
				self.setTile(x,y,code)
	
	def setSize(self, w, h):
		print "Layer %s setting size : %s %s" % (self.name, w, h)
		self.oldTiles = self.tiles
		self.tiles = [] # [x][y] : code
		self.w = w
		self.h = h
		
		for x in range(self.w):
			line = []
			for y in range(self.h):
				if len(self.oldTiles)>x and len(self.oldTiles[0])>y:
					#print "copying tile %s %s (max = %s %s)" % (x, y, len(self.oldTiles), len(self.oldTiles[0]))
					line.append(self.oldTiles[x][y])
				else:
					line.append("gggg")
		
			self.tiles.append(line)
			
		
	def setData(self, data):
		tilecodes = data.split(",")
		if len(tilecodes) != self.w * self.h:
			print "data not matching width and height"
			return False
		n = 0
		for x in range(self.w):
			for y in range(self.h):
				self.setTile(x, y, tilecodes[n])
				n +=1
	
	def getSaveData(self):
		data = []
		for x in range(self.w):
			for y in range(self.h):
				data.append(self.getTile(x, y))
		data = str(data)
		data = data.replace("[", "")
		data = data.replace("]", "")
		data = data.replace("'", "")
		data = data.replace('"', '')
		data = data.replace(' ', '')
		return data

class MapWarp(pygame.Rect):
	def __init__(self, name, x, y, w, h, targetMapName, destX, destY):
		self.name = name
		# x, y, w, h, destX, destY are in pixels
		pygame.Rect.__init__(self, (x, y, w, h))
		self.targetMap = targetMapName
		self.destX = destX
		self.destY = destY

class GameMap:
	def __init__(self, server, filename=None):
		self._server = server
		self.filename = filename
		
		self.tileWidth = 16
		self.tileHeight = 16
		self.layers = {} # name : MapLayer
		self.name = None
		
		self.mobs = {}
		self.players = {}
		self.warps = []
		
		if self.filename:
			self.load(self.filename)
			
	def addLayer(self, name):
		self.layers[name] = MapLayer(name, self.w, self.h, self.tileWidth, self.tileHeight)
		
	def addWarp(self, name, x, y, w, h, targetMapName, destX, destY):
		# x, y, w, h, destX, destY are in tiles
		warp = MapWarp(name, x*self.tileWidth, y*self.tileHeight, w*self.tileWidth, h*self.tileHeight, targetMapName, destX*self.tileWidth, destY*self.tileHeight)
		
		self.warps.append(warp)
		
	def getSaveData(self):
		if not self.name:
			if self.filename:
				self.name = self.filename
			else:
				self.name = "defaultMapName"
		
		data = ""
		data = data + "name = " + str(self.name) + "\n"
		data = data + "w = " + str(self.w) + "\n"
		data = data + "h = " + str(self.h) + "\n"
		
		for layerName in self.layers:
			data = data + layerName + " = " + str(self.layers[layerName].getSaveData()) + "\n\n"
		return data
		
	def save(self, filename):
		self.filename = filename
		f = open(filename, "w")
		f.write(self.getSaveData())
		f.close()
		print "Map saved in %s" % (filename)
		
	def load(self, filename):
		self.filename = filename
		content = open(filename).read()
		for line in content.split("\n"):
			line = line.strip()
			if len(line)<2:
				continue
			if line[0]== '#':
				continue
				
			if ":" in line:
				if len(line.split(":"))!=2: continue
				key , value = line.split(":")
				key = key.strip()
				value = value.strip()
				
				if key == "name":
					self.name = value
					
				if key == "file":
					self.loadTileData(value)
					
				if key == "warp":
					items = value.split(",")
					if len(items)!=8:
						continue
					for i in range(8):
						items[i] = items[i].strip()
					warpName = items[0]
					x = int(items[1])
					y = int(items[2])
					w = int(items[3])
					h = int(items[4])
					targetMap = items[5]
					destX = int(items[6])
					destY = int(items[7])
					
					self.addWarp(warpName, x, y, w, h, targetMap, destX, destY)
					
		
	def loadTileData(self, filename):	
		self.filename = filename
		content = open(filename).read()
		for line in content.split("\n"):
			line = line.strip()
			if len(line)<2:
				continue
			if "=" in line:
				if len(line.split("="))!=2: continue
				key , value = line.split("=")
				if key.strip() == "name":
					#self.name = value.strip()
					pass
				elif key.strip() == "w":
					self.w = int(value.strip())
				elif key.strip() == "h":
					self.h = int(value.strip())
				else:
					codes = value.split(',')
					if len(codes) == self.w * self.h:
						layerName = key.strip()
						value = value.strip()
						#print "Loading layer %s" % (layerName)
						self.addLayer(layerName)
						self.layers[layerName].setData(value)
		self.makeCollisionGrid()
		#print "Loaded map : %s" % (self.name)
		
	def makeCollisionGrid(self):
		if not self.filename:return False
		self.addLayer("collision")
		for x in range(self.w):
			for y in range(self.h):
				if self.layers["ground"].getTile(x, y) == "wwww":
					self.layers["collision"].tiles[x][y] = 1
				else:
					self.layers["collision"].tiles[x][y] = 0
		
		
	def isValidPos(self, x, y):
		if (0<=x<self.w) and (0<=y<self.h):
			return True
		return False
		
	def setSize(self, x, y):
		for layerName in self.layers:
			self.w = x
			self.h = y
			self.layers[layerName].setSize(x, y)
			
	def clearTile(self, layerName, x, y):
		self.layers[layerName].clearTile(x, y)
		
	def setTile(self, layerName, x, y, code):
		if not layerName in self.layers:return
		if not self.isValidPos(x, y):return
		if code == self.layers[layerName].getTile(x, y):return
		
		
		self.layers[layerName].setTile(x, y, code)
		if layerName == "collision":
			return
		
		# check tile up left
		if self.isValidPos(x-1, y-1):
			oldCode = self.layers[layerName].getTile(x-1, y-1)
			newCode = oldCode[0:3] + code[0]
			self.layers[layerName].setTile(x-1, y-1, newCode)
			
			
		# check tile up
		if self.isValidPos(x, y-1):
			oldCode = self.layers[layerName].getTile(x, y-1)
			newCode = oldCode[0:2] + code[0:2]
			self.layers[layerName].setTile(x, y-1, newCode)
			
		# check tile up right
		if self.isValidPos(x+1, y-1):
			oldCode = self.layers[layerName].getTile(x+1, y-1)
			newCode = oldCode[0:2] + code[1] + oldCode[3]
			self.layers[layerName].setTile(x+1, y-1, newCode)
			
		# check tile left
		if self.isValidPos(x-1, y):
			oldCode = self.layers[layerName].getTile(x-1, y)
			newCode = oldCode[0] + code[1] + oldCode[2] + code[3]
			self.layers[layerName].setTile(x-1, y, newCode)
			
		# check tile right
		if self.isValidPos(x+1, y):
			oldCode = self.layers[layerName].getTile(x+1, y)
			newCode = code[0] + oldCode[1] + code[2] + oldCode[3]
			self.layers[layerName].setTile(x+1, y, newCode)
			
		# check tile down left
		if self.isValidPos(x-1, y+1):
			oldCode = self.layers[layerName].getTile(x-1, y+1)
			newCode = oldCode[0] + code[2] + oldCode[2:4]
			self.layers[layerName].setTile(x-1, y+1, newCode)
			
		# check tile down
		if self.isValidPos(x, y+1):
			oldCode = self.layers[layerName].getTile(x, y+1)
			newCode = code[0:2] + oldCode[2:4]
			self.layers[layerName].setTile(x, y+1, newCode)
			
		# check tile down right
		if self.isValidPos(x+1, y+1):
			oldCode = self.layers[layerName].getTile(x+1, y+1)
			newCode = code[0] + oldCode[1:4]
			self.layers[layerName].setTile(x+1, y+1, newCode)
			
	
	def tileCollide(self, x, y): # tile position collide test
		if not self.isValidPos(x, y):
			return True
		if self.layers["collision"].tiles[x][y]>0:
			return True
		return False
		
	def posCollide(self, x, y): # pixel position collide test
		return self.tileCollide(int(x)/self.tileWidth, int(y)/self.tileHeight)
		
	
	def addPlayer(self, playerId, x, y):
		if playerId not in self.players:
			self.players[playerId]=Player(playerId, self, x, y)
			
	def delPlayer(self, playerName):
		del self.players[playerName]
	
	def sendPlayerUpdateMove(self, playerName):
		player = self.players[playerName]
		self._server.SendPlayerUpdateMove(self.name, playerName, player.x, player.y, player.dx, player.dy)
	
	def getNewMobId(self):
		id = "mob_"
		n = 1
		while id + str(n) in self.mobs:
			n +=1
		return id + str(n)
	
	def addMob(self, mobId, x, y):
		newId = self.getNewMobId()
		self.mobs[newId]=Mob(newId, mobId, self, x, y)
		#self.mobs[mob.id].setPos(x, y)
	
	def delMob(self, mobId):
		del self.mobs[mobId]
	
	def sendMobUpdateMove(self, mobId):
		mob = self.mobs[mobId]
		self._server.SendMobUpdateMove(self.name, mobId, mob.x, mob.y, mob.dx, mob.dy)
		
	def update(self, dt):
		for player in self.players.values():
			player.update(dt)
			for warp in self.warps:
				if warp.colliderect(player.mapRect):
					#print "Player %s entered in warp %s (leading to %s : %s/%s)" % (player.id, warp.name, warp.targetMap, warp.destX, warp.destY)
					self._server.warpPlayer(player.id, warp.targetMap, warp.destX, warp.destY)
					
		for mob in self.mobs.values():
			mob.update(dt)
