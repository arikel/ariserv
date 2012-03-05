#!/usr/bin/python
# -*- coding: utf8 -*-


class FSM(object):
	def __init__(self):
		self.state = "Default"
		
	def request(self, state):
		self.setState(state)
		
	def setState(self, state):
		exitFn = "exit" + self.state
		if hasattr(self, exitFn):
			getattr(self, exitFn)()
		
		self.state = state
		enterFn = "enter" + self.state
		if hasattr(self, enterFn):
			getattr(self, enterFn)()

class MobAI(FSM):
	def __init__(self):
		self.state = "Idle"
		
	def enterIdle(self):
		print "Mob entered idle state."
		
	def exitIdle(self):
		print "Mob exited idle state."
		
	def enterMove(self):
		print "Mob started to move."
		
	def exitMove(self):
		print "Mob stopped moving."
		
