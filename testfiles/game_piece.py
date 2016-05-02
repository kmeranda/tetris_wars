#pygame imports
import sys
import os
from random import choice
import pygame
from pygame.locals import *

#twisted imports
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.tcp import Port
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
from twisted.internet.task import LoopingCall

class CurrentPiece(pygame.sprite.Sprite):
	def __init__(self):
		shapes = ['O', 'I', 'S', 'Z', 'L', 'J', 'T']
		self.shape = choice(shapes)	# randomly choose shape for piece
		print self.shape
		self.xpos = []
		self.ypos = []
		if self.shape=='O':
			self.xpos = [4,5,4,5]
			self.ypos = [19,19,18,18]
		elif self.shape=='I':
			self.xpos = [4,4,4,4]
			self.ypos = [19,18,17,16]
		elif self.shape=='S':
			self.xpos = [3,4,4,5]
			self.ypos = [18,18,19,19]
		elif self.shape=='Z':
			self.xpos = [3,4,4,5]
			self.ypos = [19,19,18,18]
		elif self.shape=='L':
			self.xpos = [4,4,4,5]
			self.ypos = [19,18,17,17]
		elif self.shape=='J':
			self.xpos = [5,5,5,4]
			self.ypos = [19,18,17,17]
		elif self.shape=='T':
			self.xpos = [3,4,5,4]
			self.ypos = [19,19,19,18]
		else:
			print 'Invalid piece type'
			exit(1)

	def tick(self):
		for i in range(4):
			self.ypos[i] -= 1

CurrentPiece()
