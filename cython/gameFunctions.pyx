#!/usr/bin/python
# -*- coding: utf-8 -*-

#from libc.math cimport sin

cdef extern from "math.h":
	double sqrt(double)
	double sin(double)
	
cdef getDist2(double x, double y, double x2, double y2):
	return sqrt((x-x2)*(x-x2) + (y-y2)*(y-y2))
	
def getDist(double x, double y, double x2, double y2):
	return getDist2(x, y, x2, y2)

def getDistRect(a, b):
	return getDist2(a.x, a.y, b.x, b.y)
