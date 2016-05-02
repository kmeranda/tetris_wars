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



## Game ##
class GameSpace:
	def __init__(self):
		# 1. init game space
		pygame.init()
		self.size = self.width, self.height = (640, 580)
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
				lc.stop()
				reactor.stop()
		# 6. tick updating - send a tick to every game object
		self.playerspace.tick()
		self.enemyspace.tick()
		# 7. screen/display updating
		self.screen.fill(self.black)
		self.screen.blit(self.playerspace.image, self.playerspace.rect)
		self.screen.blit(self.enemyspace.image, self.enemyspace.rect)
		self.screen.blit(self.playerspace.board.squareImage, self.playerspace.board.squareRect)
		pygame.display.flip()


## PLAYER ##
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
		self.image = pygame.Surface((250,500))
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.center = (self.xpos, self.ypos)
		self.board = Board(self) #initialize board
	def tick(self):
		#should be called when a piece lands
		self.board.addPiece()
		self.board.createSquares()
		if self.num == 1:
			self.color = (255,255,255)
			self.image.fill(self.color)
			self.rect = self.image.get_rect()
			self.rect.center = (self.xpos, self.ypos)


## BOARD ##
class Board(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.width = 10
		self.height = 20
		self.array = [[0 for x in range(self.width)] for y in range(self.height)]
	def createSquares(self):
		for x in range(self.width):
			for y in range(self.height):
				if self.array[y][x] == 1:
					self.squareColor = (255, 0, 0)
					self.squareImage = pygame.Surface((25,25))
					self.squareImage.fill(self.squareColor)
					self.squareRect = self.squareImage.get_rect()
					self.squareRect.center = ((15+(12.5*x)),(40+(12.5*y)))
	def addPiece(self): #this is where a full piece should be added to the array
		self.array[0][0] = 1
		self.array[1][1] = 1



## SERVER CONNECTIONS ##
class ClientConnection(Protocol):
	def connectionMade(self):
		print "New connection made:", HOST, "port", PLAYER_PORT
	def dataReceived(self, data):
		print "Received data:", data
	def connectionLost(self, reason):
		print "Lost connection with", HOST, "port", PLAYER_PORT

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
