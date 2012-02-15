#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
from time import sleep
#from weakref import WeakKeyDictionary

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
		self.nickname = "anonymous"
		self.name = "none"
		Channel.__init__(self, *args, **kwargs)
	
	def Close(self):
		self._server.DelPlayer(self)
	
	##################################
	### Network specific callbacks ###
	##################################
	#-------------------------------------------------------------------
	# on server receive from client self.nickname :
	#-------------------------------------------------------------------
	def Network_position(self, data):
		#print "Pos msg to send to client : %s" % (data)
		self._server.SendToAll({"action": "position", "message": data['message'], "who": self.nickname, "x":data['x'], "y":data['y']})
		
	def Network_update_move(self, data):
		#print "Pos msg to send to client : %s" % (data)
		
		self._server.SendToAll({"action": "position", "message": data['message'], "who": self.nickname, "x":data['x'], "y":data['y']})
	
	def Network_public_message(self, data):
		self._server.SendToAll({"action": "public_message", "message": data['message'], "who": self.nickname})
		
	def Network_private_message(self, data):
		if data["target"] in self._server.players:
			self._server.SendTo(data["target"], {"action": "private_message", "message": data['message'], "who": self.nickname})
		else:
			msg = "%s not connected" % (data["target"])
			self._server.SendTo(self.nickname, {"action": "private_message", "message": msg, "who": 'server'})
	
	def Network_nickname(self, data):
		self.nickname = data['nickname']
		self.name = data['nickname']
		#if self.name != "anonymous":
		self._server.SendPlayers()
		self._server.players[self.name] = self
		#if "none" in self._server.players:
		#	del self._server.players["none"]
		
	def Network_login(self, data):
		self.name = data['nickname']
		self.password = data['password']
		if self._server.db.checkLogin(self.name, self.password):
			self._server.players[self.name] = self
			self._server.SendPlayers()
			if "none" in self._server.players:
				del self._server.players["none"]
	
class GameServer(Server):
	channelClass = ClientChannel
	
	def __init__(self, *args, **kwargs):
		Server.__init__(self, *args, **kwargs)
		self.playerChannels = {}#WeakKeyDictionary()
		self.players = {}
		self.db = dbHandler("db/essai.db")
		self.map = MapBase("maps/001-1.tmx")
		
		print 'Server launched'
	
	def Connected(self, channel, addr):
		self.AddPlayer(channel)
	
	def AddPlayer(self, player):
		print "New Player" + str(player.addr) + " name : " + player.name
		self.playerChannels[player] = True
		
		
		self.SendPlayers()
		print "players", [p for p in self.playerChannels]
	
	def DelPlayer(self, player):
		print "Deleting Player" + str(player.addr)
		del self.playerChannels[player]
		self.SendPlayers()
	
	#-------------------------------------------------------------------
	# generic purpose server to client
	#-------------------------------------------------------------------
	
	def SendTo(self, playerName, data):
		self.players[playerName].Send(data)
	
	def SendToAll(self, data):
		[p.Send(data) for p in self.playerChannels]
	
	def SendToList(self, playerList, data):# list of players names to send to
		[self.players[p].Send(data) for p in self.playerList]
	
	def Launch(self):
		while True:
			self.Pump()
			sleep(0.0001)
	
	#-------------------------------------------------------------------
	# server send to client
	#-------------------------------------------------------------------
	def SendPlayers(self):
		self.SendToAll({"action": "players", "players": [p.nickname for p in self.playerChannels], "who": "server"})
		
	
# get command line argument of server, port
if len(sys.argv) != 2:
	print "Usage:", sys.argv[0], "host:port"
	print "e.g.", sys.argv[0], "localhost:31425"
else:
	host, port = sys.argv[1].split(":")
	s = GameServer(localaddr=(host, int(port)))
	s.Launch()

