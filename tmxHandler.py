#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from xml.dom import minidom, Node
import base64
import gzip
import StringIO
import os.path
import pygame

#-------------------------------------------------------------------------------
def decode_base64(in_str):
	return base64.decodestring(in_str)

def encode_base64(in_str):
	return base64.encodestring(in_str)
	
def decompress_gzip(in_str):
	compressed_stream = StringIO.StringIO(in_str)
	gzipper = gzip.GzipFile(fileobj=compressed_stream)
	return gzipper.read()
	
def compress_gzip(in_str):
	compressed_stream = StringIO.StringIO()
	gzipper = gzip.GzipFile(fileobj=compressed_stream, mode="wb")
	gzipper.write(in_str)
	gzipper.close()
	return compressed_stream.getvalue()
	
def getCode(val):
	code = chr(int(val & 255))
	code = code + chr(int((val>>8) & 255))
	code = code + chr(int((val>>16) & 255))
	code = code + chr(int((val>>24) & 255))
	return code
	
def decode(encoded_content):
	s = encoded_content
	if encoded_content:
		s = decode_base64(s)
		s = decompress_gzip(s)
	#print "Content after decode and decompress : %s" % (s)
	decoded_content = []
	for idx in xrange(0, len(s), 4):
		val = ord(str(s[idx])) | (ord(str(s[idx + 1])) << 8) | \
			 (ord(str(s[idx + 2])) << 16) | (ord(str(s[idx + 3])) << 24)
		decoded_content.append(val)
	return decoded_content
	
def encode(content_list):
	"Encodes an array of ints corresponding to tiles id"
	coded_content = ""
	for n in content_list:
		coded_content = coded_content + getCode(n)
	coded_content = compress_gzip(coded_content)
	coded_content = encode_base64(coded_content)
	return coded_content
	

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
