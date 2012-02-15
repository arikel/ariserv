#!/usr/bin/python
# -*- coding: utf8 -*-

import pygame
import sys
import math
import re
import string



def ustr(o):
	"""This function is like 'str', except that it can return unicode as well"""
	if isinstance(o, unicode):
		o.encode("utf-8")
		return o
	#if isinstance(o, basestring):
	#	return o.value()
	return unicode(str(o.encode("utf-8")))

def getDist(a, b):
	return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2)
