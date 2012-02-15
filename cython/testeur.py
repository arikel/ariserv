#!/usr/bin/python
# -*- coding: utf-8 -*-
import pygame

from gameFunctions import getDist, getDistRect

pygame.init()
a = pygame.Rect(5.0,5.0,1,1)
b = pygame.Rect(5.0,25.0,1,1)

currentTime = pygame.time.get_ticks()

for i in range(100000):
	b.x = i
	#getDist(a.x, a.y, b.x, b.y)
	getDistRect(a,b)
	
elapsed = (pygame.time.get_ticks() - currentTime)/100.0
print "Time spent : %s" % (elapsed)
pygame.quit()
