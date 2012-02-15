#!/usr/bin/python
# -*- coding: utf8 -*-
import pygame
from tmxHandler import *

class TileLayer(object):
	def __init__(self, name, width, height, data = []):
		self.name = name
		self.width = width
		self.height = height
		self.data = data
		#self.tiles = [] # [x][y] -> gid
		self.clearTiles()
		self.makeTiles()
		
	def clearTiles(self):
		self.tiles = []
		for x in range(self.width):
			col = []
			for y in range(self.height):
				col.append(0)
			self.tiles.append(col)
	
	def makeTiles(self):
		X = 0
		Y = 0
		for gid in self.data:
			#if gid != 0:
			self.tiles[X][Y]=gid
			X += 1
			if X == self.width:
				X = 0
				Y += 1

#-------------------------------------------------------------------------------
class TmxMapData(object):
	def __init__(self):
		self.myMap = None
		
		
	def load(self, filename):
		self.myMap = self.parseMap(filename)
		self.width = int(self.myMap.getAttribute("width")) # width in tiles
		self.height = int(self.myMap.getAttribute("height")) # height in tiles
		self.tileWidth = int(self.myMap.getAttribute("tilewidth"))
		self.tileHeight = int(self.myMap.getAttribute("tileheight"))
		
		self.maxTileWidth = 0
		self.maxTileHeight = 0
		
		self.layerImageWidth = self.width * self.tileWidth
		self.layerImageHeight = self.height * self.tileHeight
		
		
	def getChildNodes(self, node, name):
		children = []
		for child in node.childNodes:
			if (child.nodeType == Node.ELEMENT_NODE and child.nodeName == name):
				children.append(child)
		return children

	def parseMap(self, filename):# return map node
		dom = minidom.parseString(open(filename, "rb").read())
		for node in self.getChildNodes(dom, "map"):
			return node
		return None
		
	def getLayerNames(self):
		data = []
		layers = self.getChildNodes(self.myMap, "layer")
		for layer in layers:
			name = layer.getAttribute("name")
			data.append(name)
		return data

	def getLayerData(self, layername):
		layers = self.getChildNodes(self.myMap, "layer")
		for layer in layers:
			name = layer.getAttribute("name")
			if name == layername:
				layerData = self.getChildNodes(layer, "data")
				return layerData[0].childNodes[0]._get_data()
		return None

	def getLayerDataDic(self, layername):
		data = {}
		layers = self.getChildNodes(self.myMap, "layer")
		for layer in layers:
			name = layer.getAttribute("name")
			if name == layername:
				layerData = self.getChildNodes(layer, "data")
				#data.append(layerData[0].childNodes[0]._get_data())
				data[layername] = layerData[0].childNodes[0]._get_data()
		return data

	


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
		if self.collisionLayer.tiles[x][y]>0:
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
		
		
