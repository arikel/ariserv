#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import sqlite3
import time

class dbHandler(object):
	def __init__(self, dbfile):
		self.dbfile = dbfile
		self.connection = sqlite3.connect(self.dbfile)
		self.cursor = self.connection.cursor()
		
	def execute(self, args):
		#print "args were : %s" % (args)
		self.cursor.execute(args)
		result = self.cursor.fetchall()
		self.connection.commit()
		return result
	
	#-------------------------------------------------------------------
	# game db init
	#-------------------------------------------------------------------	
	def initTables(self):
		self.createPlayersTable()
		
	def reset(self):
		self.execute("""drop table players""")
		self.execute("""drop table characters""")
		self.execute("""drop table items""")
		self.execute("""drop table inventory""")
	
	#-------------------------------------------------------------------
	# players table
	#-------------------------------------------------------------------
		
	def createPlayerTable(self):
		self.execute("""create table players(
			id integer primary key autoincrement,
			name text,
			password text,
			date text)""")
		
	def addPlayer(self, name, password):
		today = time.strftime("%Y%m%d%H%M")
		msg = """insert into players values(NULL, '%s', '%s', '%s')""" % (name, password, today)
		self.execute(msg)
		
	def delPlayer(self, name):
		msg = """remove from players where name='%s'""" % (name)
		self.execute(msg)
		
	def getPlayer(self, name):
		info = self.execute("""select * from players where name = '%s'""" % (name))
		if len(info)>0:
			return info[0]
		return None
		
	
	def hasPlayer(self, name):
		if len(self.execute("""select * from players where name = '%s'""" % (name)))>0:
			return True
		return False
	
	def checkLogin(self, name, password):
		res = self.execute("""select * from players where name = '%s'""" % (name))
		if len(res)>0:
			if res[2]==password:
				return True
		return False
	
	#-------------------------------------------------------------------
	# characters
	#-------------------------------------------------------------------
	
	def createCharTable(self):
		self.execute("""create table characters(
			
			)""")
	
	#-------------------------------------------------------------------
	# items, equipment, inventory, storage
	#-------------------------------------------------------------------
	
	def createItemTable(self):
		self.execute("""create table items(
			
			)""")
		
	def createInventoryTable(self):
		self.execute("""create table inventory(
			ownerName text,
			itemId integer,
			quantity integer
			)""")
			
	
#dbhandler = dbHandler("db/essai.db")