#pygame imports
import sys
import os
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

#twisted port/host variables
HOST = 'student02.cse.nd.edu'
PLAYER_PORT = 40011

class GameSpace:
	def __init__(self):
		# 1. init game space
		pygame.init()
		self.size = self.width, self.height = (640, 480)
		self.screen = pygame.display.set_mode(self.size)
		self.black = (0,0,0)

		#2. init game objects
		self.clock = pygame.time.Clock()
		self.playerspace = PlayerSpace(1, self)
		self.enemyspace = PlayerSpace(2, self)

	# 3. start game loop
	def game_loop_iterate(self):
		# 4. clock tick regulation (framerate)
		self.clock.tick(60)
		# 5. user input reading
		for event in pygame.event.get():
			if event.type == QUIT:
				sys.exit()
		# 6. tick updating - send a tick to every game object
		self.playerspace.tick()
		self.enemyspace.tick()
		# 7. screen/display updating
		self.screen.fill(self.black)
		self.screen.blit(self.playerspace.image, self.playerspace.rect)
		self.screen.blit(self.enemyspace.image, self.enemyspace.rect)
		pygame.display.flip()

class PlayerSpace(pygame.sprite.Sprite):
	def __init__(self, player_num, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.ypos = gs.height/2
		self.num = player_num
		if self.num == 1:
			self.xpos = 140
		else:
			self.xpos = 500
		self.color = (185,185,185)
		self.image = pygame.Surface((250,400))
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.center = (self.xpos, self.ypos)
	def tick(self):
		if self.num == 1:
			self.color = (255,255,255)
			self.image.fill(self.color)
			self.rect = self.image.get_rect()
			self.rect.center = (self.xpos, self.ypos)

class ClientConnection(Protocol):
	def connectionMade(self):
		print "New connection made:", HOST, "port", PLAYER_PORT
	def dataReceived(self, data):
		print "Received data:", data
	def connectionLost(self, reason):
		print "Lost connection with", HOST, "port", PLAYER_PORT
		reactor.stop() #I think we should keep this??

class ClientConnFactory(ClientFactory):
	def buildProtocol(self,addr):
		return ClientConnection()

if __name__ == '__main__':
	gs = GameSpace()
	lc = LoopingCall(gs.game_loop_iterate)	
	lc.start(1/60)
	#try:
	reactor.connectTCP(HOST, PLAYER_PORT, ClientConnFactory())
	#except:
	#	PLAYER_PORT = 40111
	#	reactor.connectTCP(HOST, PLAYER_PORT, ClientConnFactory())
	reactor.run()
	lc.stop()
