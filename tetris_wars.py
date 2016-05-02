### PLAYER 1 ###

#pygame imports
import sys
import os
import pygame
from pygame.locals import *
from random import choice

#twisted imports
from twisted.internet.protocol import ClientFactory
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.tcp import Port
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue
from twisted.internet.task import LoopingCall
import cPickle as pickle

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
			elif event.type == KEYDOWN:
				if event.key == K_LEFT:
					self.playerspace.move(-1)
				elif event.key == K_RIGHT:
					self.playerspace.move(1)
				elif event.key == K_UP:
					self.playerspace.place()
				elif event.key == K_SPACE:
					self.playerspace.rotate()
		# 6. tick updating - send a tick to every game object
		self.playerspace.tick()
		self.enemyspace.tick()
		# 7. screen/display updating
		self.screen.fill(self.black)
		self.screen.blit(self.playerspace.image, self.playerspace.rect)
		self.screen.blit(self.enemyspace.image, self.enemyspace.rect)
		for i in range(0, len(self.playerspace.board.images)):
			self.screen.blit(self.playerspace.board.borders[i], self.playerspace.board.borderRects[i])
			self.screen.blit(self.playerspace.board.images[i], self.playerspace.board.rects[i])
		for i in range(0, len(self.enemyspace.board.images)):
			self.screen.blit(self.enemyspace.board.borders[i], self.enemyspace.board.borderRects[i])
			self.screen.blit(self.enemyspace.board.images[i], self.enemyspace.board.rects[i])
		for i in range(4):
			self.screen.blit(self.playerspace.curr_piece.borders[i], self.playerspace.curr_piece.borderRects[i])
			self.screen.blit(self.playerspace.curr_piece.images[i], self.playerspace.curr_piece.rects[i])
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
		self.piece_landed = False
		self.color = (185,185,185)
		self.image = pygame.Surface((260,520))
		self.image.fill(self.color)
		self.rect = self.image.get_rect()
		self.rect.center = (self.xpos, self.ypos)
		self.board = Board(self.num, self) #initialize board
		self.curr_piece = CurrentPiece(self)
	def move(self, dir):
		edge = False	# check so that you don't go out of bounds
		for i in range(4):
			self.curr_piece.xpos[i] += dir
			if self.curr_piece.xpos[i]<0 or self.curr_piece.xpos[i]>=self.board.width:
				edge = True
		if edge:
			for i in range(4):
				self.curr_piece.xpos[i] -= dir
			

	def place(self):
		# curr_piece tick logic looped until it hits the bottom
		while not self.piece_landed:
			self.curr_piece.tick()
			self.piece_landed = self.collision(self.board.boardArray, self.curr_piece)
		for i in range(4):
			x = self.curr_piece.xpos[i]
			y = self.curr_piece.ypos[i]
			s = self.curr_piece.shape
			self.board.boardArray[y][x] = s
		self.curr_piece = CurrentPiece(self)	# re-init curr_piece
		self.piece_landed = False
		
	
	def rotate(self):
		if self.curr_piece.shape != 'O':	# cannot rotate square
			x_arr = self.curr_piece.xpos
			y_arr = self.curr_piece.ypos
			x = x_arr[2]	# rotate about 3rd square
			y = y_arr[2]
			# get distances from 
			x_dist = [(x_arr[i]-x) for i in range(4)]
			y_dist = [(y_arr[i]-y) for i in range(4)]
			self.curr_piece.xpos = [(x-y_dist[i]) for i in range(4)]
			self.curr_piece.ypos = [(y+x_dist[i]) for i in range(4)]
	
	def collision(self, board, piece):
		num = 0
		# check for collisions
		for i in range(4):
			if piece.ypos[i]-1>=0:
				if board[piece.ypos[i]-1][piece.xpos[i]]==0:
					num +=1
		return (num != 4)	# return True if there is a collision
		
	def tick(self):
		self.board.createSquares() #visually interpret board
		#update current piece only on own board
		if self.num == 1:
			self.board.addPiece()
			# curr_piece tick logic
			self.piece_landed = self.collision(self.board.boardArray, self.curr_piece)
			if self.piece_landed:	# add curr_piece to boardArray
				for i in range(4):
					x = self.curr_piece.xpos[i]
					y = self.curr_piece.ypos[i]
					s = self.curr_piece.shape
					self.board.boardArray[y][x] = s
				self.curr_piece = CurrentPiece(self)	# re-init curr_piece
				self.piece_landed = False
			
			else:	# move curr_piece down
				self.curr_piece.tick()
			self.color = (255,255,255)
			self.image.fill(self.color)
			self.rect = self.image.get_rect()
			self.rect.center = (self.xpos, self.ypos)


## BOARD ##
class Board(pygame.sprite.Sprite):
	def __init__(self, player_num, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.width = 10
		self.height = 20
		if (player_num == 1):
			self.start_xCoord = 10
		elif (player_num == 2):
			self.start_xCoord = 370
		self.boardArray = [[0 for x in range(self.width)] for y in range(self.height)]
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
	def createSquares(self):
		for x in range(self.width):
			for y in range(self.height):
				#set square color depending on contents of array
				if (self.boardArray[y][x] == 'O'): #yellow
					self.squareColor = (255, 255, 0)
				elif (self.boardArray[y][x] == 'I'): #teal
					self.squareColor = (0, 255, 255)
				elif (self.boardArray[y][x] == 'S'): #red
					self.squareColor = (255, 0, 0)
				elif (self.boardArray[y][x] == 'Z'): #green
					self.squareColor = (34, 139, 34)
				elif (self.boardArray[y][x] == 'L'): #orange
					self.squareColor = (255, 140, 0)
				elif (self.boardArray[y][x] == 'J'): #blue
					self.squareColor = (0, 0, 255)
				elif (self.boardArray[y][x] == 'T'): #purple
					self.squareColor = (160, 32, 240)
				if (self.boardArray[y][x] != 0): #create square, rect, and border for all filled coordinates
					self.centerx = self.start_xCoord+8+(24*x)
					self.centery = 38+(24*(self.height-y))
					self.squareImage = pygame.Surface((24,24))
					self.squareImage.fill(self.squareColor)
					self.images.append(self.squareImage)
					self.squareRect = self.squareImage.get_rect()
					self.squareRect.center = (self.centerx, self.centery)
					self.rects.append(self.squareRect)
					self.border = pygame.Surface((26,26))
					self.border.fill((0,0,0))
					self.borders.append(self.border)
					self.borderRect = self.border.get_rect()
					self.borderRect.center = (self.centerx, self.centery)
					self.borderRects.append(self.borderRect)
	def moveDown(self): #should reinit image and rect arrays
		pass
	def addPiece(self): #this is where a full piece should be added to the array
		self.boardArray[0][0] = 'O'
		self.boardArray[1][1] = 'I'
		self.boardArray[2][2] = 'S'
		self.boardArray[3][3] = 'Z'
		self.boardArray[4][4] = 'L'
		self.boardArray[5][5] = 'J'
		self.boardArray[6][6] = 'T'


## CURRENT PIECE ##
class CurrentPiece(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		shapes = ['O', 'I', 'S', 'Z', 'L', 'J', 'T']
		self.shape = choice(shapes)	# randomly choose shape for piece
		self.xpos = [0,0,0,0]
		self.ypos = [0,0,0,0]
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
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
		self.createSquares()

	def tick(self):
		# no collisions = move down
		for i in range(4):
			self.ypos[i] -= 1
		# update graphics
		self.createSquares()

	def createSquares(self):
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
		for x in range(4):
			#set square color depending on contents of array
			if (self.shape == 'O'): #yellow
				self.squareColor = (255, 255, 0)
			elif (self.shape == 'I'): #teal
				self.squareColor = (0, 255, 255)
			elif (self.shape == 'S'): #red
				self.squareColor = (255, 0, 0)
			elif (self.shape == 'Z'): #green
				self.squareColor = (34, 139, 34)
			elif (self.shape == 'L'): #orange
				self.squareColor = (255, 140, 0)
			elif (self.shape == 'J'): #blue
				self.squareColor = (0, 0, 255)
			elif (self.shape == 'T'): #purple
				self.squareColor = (160, 32, 240)

			self.centerx = 18+(24*self.xpos[x])
			self.centery = 38+(24*(20-self.ypos[x]))
			self.squareImage = pygame.Surface((24,24))
			self.squareImage.fill(self.squareColor)
			self.images.append(self.squareImage)
			self.squareRect = self.squareImage.get_rect()
			self.squareRect.center = (self.centerx, self.centery)
			self.rects.append(self.squareRect)
			self.border = pygame.Surface((26,26))
			self.border.fill((0,0,0))
			self.borders.append(self.border)
			self.borderRect = self.border.get_rect()
			self.borderRect.center = (self.centerx, self.centery)
			self.borderRects.append(self.borderRect)
	

## SERVER CONNECTIONS ##
class ClientConnection(Protocol):
	def __init__(self, gs):
		self.gs = gs
	def connectionMade(self):
		print "New connection made:", HOST, "port", PLAYER_PORT
		self.sendData()
	def dataReceived(self, data): #receive other gamespace from server
		#print "Received data"
		self.gs.enemyspace.board.boardArray = pickle.loads(data)
		self.sendData()
	def sendData(self):
		array = pickle.dumps(self.gs.playerspace.board.boardArray) #pickle array to string
		self.transport.write(array) #send updated gamespace to server
	def connectionLost(self, reason):
		print "Lost connection with", HOST, "port", PLAYER_PORT

class ClientConnFactory(ClientFactory):
	def __init__(self, gs):
		self.gs = gs
	def buildProtocol(self,addr):
		return ClientConnection(self.gs)



if __name__ == '__main__':
	gs = GameSpace()
	lc = LoopingCall(gs.game_loop_iterate)	
	lc.start(1/60)
	reactor.connectTCP(HOST, PLAYER_PORT, ClientConnFactory(gs))
	reactor.run()
