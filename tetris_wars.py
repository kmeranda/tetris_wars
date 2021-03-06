# Kim Forbes & Kelsey Meranda
# CSE 30332
# PyGame + Twisted Final Project
# 4 May 2016

## Tetris Wars # 
### PLAYER 1 ###

#pygame imports
import sys
import os
import pygame
from pygame.locals import *
from random import choice, randint

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
BOARD_PORT = 40011
SCORE_PORT = 40211



## Game ##
class GameSpace:
	def __init__(self):
		# 1. init game space
		pygame.init()
		self.size = self.width, self.height = (640, 640)
		self.screen = pygame.display.set_mode(self.size)
		self.black = (0,0,0)

		#2. init game objects
		self.clock = pygame.time.Clock()
		self.playerspace = PlayerSpace(1, self)
		self.enemyspace = PlayerSpace(2, self)
		#text objects
		self.titleFont = pygame.font.SysFont("monospace", 50)
		self.title = self.titleFont.render("Tetris Wars", 1, (255,255,255))
		self.playerFont = pygame.font.SysFont("monospace", 30)
		self.playerHeader = self.playerFont.render("Player 1", 1, (255,255,255))
		self.playerBoardCaption = self.playerFont.render("Player's Board", 1, (255,255,255))
		self.opponentBoardCaption = self.playerFont.render("Opponent's Board", 1, (255,255,255))
		self.scoreCaption = self.playerFont.render("Score: ", 1, (255,255,255))
		self.winFont = pygame.font.SysFont("monospace", 50)
		self.winFont.set_bold(True)
		#animations
		self.winAnimation = None		
		
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
		#titles
		self.screen.blit(self.title, (225, 3))
		self.screen.blit(self.playerHeader, (280, 40))
		#board backgrounds
		self.screen.blit(self.playerspace.image, self.playerspace.rect)
		self.screen.blit(self.enemyspace.image, self.enemyspace.rect)
		#contents of boards
		for i in range(0, len(self.playerspace.board.images)):
			self.screen.blit(self.playerspace.board.borders[i], self.playerspace.board.borderRects[i])
			self.screen.blit(self.playerspace.board.images[i], self.playerspace.board.rects[i])
		for i in range(0, len(self.playerspace.board.powerups)):
			self.screen.blit(self.playerspace.board.powerups[i], self.playerspace.board.powerupRects[i])
		for i in range(0, len(self.enemyspace.board.images)):
			self.screen.blit(self.enemyspace.board.borders[i], self.enemyspace.board.borderRects[i])
			self.screen.blit(self.enemyspace.board.images[i], self.enemyspace.board.rects[i])
		for i in range(0, len(self.enemyspace.board.powerups)):
			self.screen.blit(self.enemyspace.board.powerups[i], self.enemyspace.board.powerupRects[i])
		for i in range(4):
			self.screen.blit(self.playerspace.curr_piece.borders[i], self.playerspace.curr_piece.borderRects[i])
			self.screen.blit(self.playerspace.curr_piece.images[i], self.playerspace.curr_piece.rects[i])
		for i in range(0, len(self.playerspace.curr_piece.powerups)):
			self.screen.blit(self.playerspace.curr_piece.powerups[i], self.playerspace.curr_piece.powerupRects[i])
		#board captions/scores
		self.screen.blit(self.playerBoardCaption, (70, 590))
		self.screen.blit(self.opponentBoardCaption, (410, 590))
		self.screen.blit(self.scoreCaption, (70, 610))
		self.screen.blit(self.scoreCaption, (410, 610))
		self.myScore = self.playerFont.render(str(self.playerspace.score), 1, (255,255,255))
		self.screen.blit(self.myScore, (140, 610))
		self.oppScore = self.playerFont.render(str(self.enemyspace.score), 1, (255,255,255))
		self.screen.blit(self.oppScore, (480, 610))
		#gameover/winner displays
		self.myStateText = ''
		self.oppStateText = ''
		self.winText = ''
		if self.playerspace.state == 1: #your game is over
			self.myStateText = 'GAME OVER'
		if self.enemyspace.state == 1: #opponent's game is over
			self.oppStateText = 'GAME OVER'
		if (self.playerspace.state + self.enemyspace.state) == 2: #if both games are over, determine winner
			if self.playerspace.score > self.enemyspace.score: #you have higher score
				self.winText = 'YOU WIN!!'
				if self.winAnimation == None:
					self.winAnimation = Fireworks(self)
			elif self.enemyspace.score > self.playerspace.score: #opp has higher score
				self.winText = 'YOU LOSE.'
				if self.winAnimation == None:
					self.winAnimation = Explosion(self)
			else: #draw
				self.winText = "IT'S A TIE."
		if self.winAnimation:
			self.winAnimation.tick()
			self.screen.blit(self.winAnimation.image, self.winAnimation.rect)
		self.myState = self.playerFont.render(self.myStateText, 1, (178,34,34))
		self.screen.blit(self.myState, (70, 320))
		self.oppState = self.playerFont.render(self.oppStateText, 1, (178,34,34))
		self.screen.blit(self.oppState, (450, 320))
		self.win = self.winFont.render(self.winText, 1, (178,34,34))
		self.screen.blit(self.win, (225, 320))
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
		self.curr_piece = CurrentPiece(self) #falling piece
		self.score = 0
		self.state = 0 #playing=0, gameover=1
	def move(self, dir):
		for i in range(4):
			self.curr_piece.xpos[i] += dir
		if self.collision(self.board.boardArray, self.curr_piece):
			for i in range(4):
				self.curr_piece.xpos[i] -= dir

	def place(self):
		# curr_piece tick logic looped until piece hits the bottom
		while not self.collision(self.board.boardArray, self.curr_piece):
			self.curr_piece.tick()
		self.curr_piece.untick() # back up one tick to legal position
		# add piece to board array
		for i in range(4):
			x = self.curr_piece.xpos[i]
			y = self.curr_piece.ypos[i]
			s = self.curr_piece.shape
			if self.curr_piece.powerup == i:
				s = s.lower()
			try:	# in case piece is above board, don't place in board
				self.board.boardArray[y][x] = s
			except:
				pass
		self.curr_piece = CurrentPiece(self)	# re-init curr_piece
		while self.collision(self.board.boardArray, self.curr_piece):	# if new piece immediately collides, then you lose
			self.state = 1	# game over state
			self.board.boardArray[self.board.height-1][self.board.width-1] = 1 	# corner of board array encoded to signal opponent of game over state
			self.curr_piece.untick()	# back up above the last piece
	
	def rotate(self):
		if self.curr_piece.shape != 'O':	# cannot rotate square
			x_arr = [self.curr_piece.xpos[i] for i in range(4)]
			y_arr = [self.curr_piece.ypos[i] for i in range(4)]
			x = x_arr[2]	# rotate about 3rd square of tetromino
			y = y_arr[2]
			# get distances from center of rotation
			x_dist = [(x_arr[i]-x) for i in range(4)]
			y_dist = [(y_arr[i]-y) for i in range(4)]
			self.curr_piece.xpos = [(x-y_dist[i]) for i in range(4)]
			self.curr_piece.ypos = [(y+x_dist[i]) for i in range(4)]
			if self.collision(self.board.boardArray, self.curr_piece): # rotate causes problems
				self.curr_piece.xpos = x_arr
				self.curr_piece.ypos = y_arr

	def collision(self, board, piece):
		for i in range(4):
			if piece.ypos[i]<0:	# collision with bottom
				return True
			if piece.xpos[i]<0 or piece.xpos[i]>len(board[i])-1: # collision with sides
				return True
			if piece.ypos[i]<len(board):	# only an issue for end game
				if board[piece.ypos[i]][piece.xpos[i]]!=0:	# collision with other piece
					return True
		return False
	
	def activate_powerup(self, num):	# powerup activated
		for i in range(0, num):
			powerupval = randint(0,4)
			if powerupval == 0: #multiply score by 2
				self.score *= 2
			else: #delete 1-4 rows
				for j in range(1, powerupval):
					del self.board.boardArray[0] # delete full row
					self.board.boardArray.append([0 for x in range(self.board.width)]) # add empty row to top
					self.score += 1

	def tick(self):
		## board tick logic ##
		self.board.createSquares() #visually interpret board
		board_return = self.board.moveDown()
		self.score += board_return[0] # delete full rows in board and increase score
		self.activate_powerup(board_return[1])
		self.state = self.board.boardArray[self.board.height-1][self.board.width-1]

		## curr_piece tick logic ##
		#update current piece only on own board
		if self.num == 1 and self.state != 1:	# piece logic only on player and only when not lost
			self.curr_piece.tick()
			self.piece_landed = self.collision(self.board.boardArray, self.curr_piece)
			if self.piece_landed:	# add curr_piece to boardArray
				# back up one tick to legal position
				self.curr_piece.untick()
				# add piece to board
				for i in range(4):
					x = self.curr_piece.xpos[i]
					y = self.curr_piece.ypos[i]
					s = self.curr_piece.shape
					if self.curr_piece.powerup == i:
						s = s.lower()
					try:
						self.board.boardArray[y][x] = s
					except:
						pass
				self.curr_piece = CurrentPiece(self)	# re-init curr_piece
				while self.collision(self.board.boardArray, self.curr_piece):	# if immediate collision with new piece then game over
					self.state = 1
					self.board.boardArray[self.board.height-1][self.board.width-1] = 1	# encode game state in corner cell of board for data transfer
					self.curr_piece.untick()
				self.piece_landed = False
			
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
		if (player_num == 1):	# current player
			self.start_xCoord = 10
		elif (player_num == 2):	# enemy player
			self.start_xCoord = 370
		self.boardArray = [[0 for x in range(self.width)] for y in range(self.height)]
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
		self.powerups = []
		self.powerupRects = []
	def createSquares(self):
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
		self.powerups = []
		self.powerupRects = []
		for x in range(self.width):
			for y in range(self.height):
				#set square color depending on contents of array
				if (self.boardArray[y][x] in ['O','o']): #yellow
					self.squareColor = (255, 255, 0)
				elif (self.boardArray[y][x] in ['I','i']): #teal
					self.squareColor = (0, 255, 255)
				elif (self.boardArray[y][x] in ['S','s']): #red
					self.squareColor = (255, 0, 0)
				elif (self.boardArray[y][x] in ['Z','z']): #green
					self.squareColor = (34, 139, 34)
				elif (self.boardArray[y][x] in ['L','l']): #orange
					self.squareColor = (255, 140, 0)
				elif (self.boardArray[y][x] in ['J','j']): #blue
					self.squareColor = (0, 0, 255)
				elif (self.boardArray[y][x] in ['T','t']): #purple
					self.squareColor = (160, 32, 240)
				if (self.boardArray[y][x] not in [0,1]): #create square, rect, and border for all filled coordinates
					self.centerx = self.start_xCoord+13+(26*x)
					self.centery = 73+(26*(self.height-(y+1)))
					#colored square
					self.squareImage = pygame.Surface((24,24))
					self.squareImage.fill(self.squareColor)
					self.images.append(self.squareImage)
					self.squareRect = self.squareImage.get_rect()
					self.squareRect.center = (self.centerx, self.centery)
					self.rects.append(self.squareRect)
					#border
					self.border = pygame.Surface((26,26))
					self.border.fill((0,0,0))
					self.borders.append(self.border)
					self.borderRect = self.border.get_rect()
					self.borderRect.center = (self.centerx, self.centery)
					self.borderRects.append(self.borderRect)
					#powerup
					if self.boardArray[y][x].lower() == self.boardArray[y][x]: #lowercase -- powerup	
						self.powerupImage = pygame.image.load("star.png")
						self.powerupImage = pygame.transform.scale(self.powerupImage, (20, 20)) #scale image larger
						self.powerups.append(self.powerupImage)
						self.powerupRect = self.powerupImage.get_rect()
						self.powerupRect.center = (self.centerx, self.centery)
						self.powerupRects.append(self.powerupRect)

	def moveDown(self): #clear full rows on board
		updateScore = 0
		powerups = 0
		for y in range(self.height):	# iterate through rows in board
			if not 0 in self.boardArray[y]:	# check for no empty space in row
				for x in range(self.width):
					if self.boardArray[y][x].islower(): # is a powerup
						powerups += 1
				del self.boardArray[y]	# delete full row
				self.boardArray.append([0 for x in range(self.width)]) # add empty row to top
				updateScore += 1
		return [updateScore, powerups]


## CURRENT PIECE ##
class CurrentPiece(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		shapes = ['O', 'I', 'S', 'Z', 'L', 'J', 'T']
		self.shape = choice(shapes)	# randomly choose shape for piece
		self.powerup =  randint(0,20)	# 0-3 indicate a power up on one of the spots, else is no powerup on the piece
		self.xpos = [0,0,0,0]
		self.ypos = [0,0,0,0]
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
		self.powerups = []
		self.powerupRects = []
		# position of initial pieces
		if self.shape in ['O','o']:
			self.xpos = [4,5,4,5]
			self.ypos = [19,19,18,18]
		elif self.shape in ['I','i']:
			self.xpos = [4,4,4,4]
			self.ypos = [19,18,17,16]
		elif self.shape in ['S','s']:
			self.xpos = [3,4,4,5]
			self.ypos = [18,18,19,19]
		elif self.shape in ['Z','z']:
			self.xpos = [3,4,4,5]
			self.ypos = [19,19,18,18]
		elif self.shape in ['L','l']:
			self.xpos = [4,4,4,5]
			self.ypos = [19,18,17,17]
		elif self.shape in ['J','j']:
			self.xpos = [5,5,5,4]
			self.ypos = [19,18,17,17]
		elif self.shape in ['T','t']:
			self.xpos = [3,4,5,4]
			self.ypos = [19,19,19,18]
		else:
			print 'Invalid piece type'
			exit(1)
		self.createSquares()

	def tick(self):
		for i in range(4):
			self.ypos[i] -= 1
		# update graphics
		self.createSquares()

	def untick(self):
		for i in range(4):
			self.ypos[i] += 1
		# update graphics
		self.createSquares()
	
	def createSquares(self):
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
		self.powerups = []
		self.powerupRects = []
		for x in range(4):
			# add default blank image
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
			self.centerx = 23+(26*self.xpos[x])
			self.centery = 73+(26*(20-(self.ypos[x]+1)))
			#colored square
			self.squareImage = pygame.Surface((24,24))
			self.squareImage.fill(self.squareColor)
			if self.ypos[x]>19:	# end pieces
				self.squareImage.fill((0,0,0))
			self.images.append(self.squareImage)
			self.squareRect = self.squareImage.get_rect()
			self.squareRect.center = (self.centerx, self.centery)
			self.rects.append(self.squareRect)
			#border
			self.border = pygame.Surface((26,26))
			self.border.fill((0,0,0))
			self.borders.append(self.border)
			self.borderRect = self.border.get_rect()
			self.borderRect.center = (self.centerx, self.centery)
			self.borderRects.append(self.borderRect)
			#powerup
		if self.powerup < 4 and self.ypos[x]<19: #lowercase -- powerup
			# center of the square with the powerup
			self.centerx = 23+(26*self.xpos[self.powerup])
			self.centery = 73+(26*(20-(self.ypos[self.powerup]+1)))
			self.powerupImage = pygame.image.load("star.png")
			self.powerupImage = pygame.transform.scale(self.powerupImage, (20, 20)) #scale image larger
			self.powerups.append(self.powerupImage)
			self.powerupRect = self.powerupImage.get_rect()
			self.powerupRect.center = (self.centerx, self.centery)
			self.powerupRects.append(self.powerupRect)
	

## EXPLOSION ##
class Explosion(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.image = pygame.image.load("explosion/frames016a.png")
		self.image = pygame.transform.scale(self.image, (600, 600)) #scale image larger
		self.rect = self.image.get_rect()
		self.rect.center = (self.gs.width/2,self.gs.height/2)
		self.frame = 0
	def tick(self):
		if self.frame < 16: #go through all frames of the explosion
			filename = 'explosion/frames{0:03d}a.png'.format(self.frame)
			self.image = pygame.image.load(filename)
			self.size = self.imageWidth, self.imageHeight = self.image.get_size()
			self.image = pygame.transform.scale(self.image, (600, 600))
			self.frame += 1
		else:
			self.image = pygame.image.load("empty.png")


## FIREWORKS ##
class Fireworks(pygame.sprite.Sprite):
	def __init__(self, gs=None):
		pygame.sprite.Sprite.__init__(self)
		self.gs = gs
		self.image = pygame.image.load("firework/fireworks00.png")
		self.image = pygame.transform.scale(self.image, (600, 600)) #scale image larger
		self.rect = self.image.get_rect()
		self.rect.center = (self.gs.width/2,self.gs.height/2)
		self.frame = 0
	def tick(self):
		if self.frame < 14: #go through all frames
			filename = 'firework/fireworks{0:02d}.png'.format(self.frame)
			self.image = pygame.image.load(filename)
			self.size = self.imageWidth, self.imageHeight = self.image.get_size()
			self.image = pygame.transform.scale(self.image, (600, 600))
			self.frame += 1
		else:
			self.image = pygame.image.load("empty.png")


## SERVER CONNECTIONS ##
class ClientBoardConnection(Protocol):
	def __init__(self, gs):
		self.gs = gs
	def connectionMade(self):
		print "New board connection made:", HOST, "port", BOARD_PORT
		self.sendData()
	def dataReceived(self, data): #receive other gamespace from server
		#print "Received data"
		self.gs.enemyspace.board.boardArray = pickle.loads(data)
		self.sendData()
	def sendData(self):
		array = [[self.gs.playerspace.board.boardArray[y][x] for x in range(self.gs.playerspace.board.width)] for y in range(self.gs.playerspace.board.height)]
		for i in range(4):
			try:
				array[self.gs.playerspace.curr_piece.ypos[i]][self.gs.playerspace.curr_piece.xpos[i]] = self.gs.playerspace.curr_piece.shape
				if i == self.gs.playerspace.curr_piece.powerup:
					array[self.gs.playerspace.curr_piece.ypos[i]][self.gs.playerspace.curr_piece.xpos[i]] = self.gs.playerspace.curr_piece.shape.lower()
			except:
				pass
		array = pickle.dumps(array)	
		self.transport.write(array) #send updated gamespace to server
	def connectionLost(self, reason):
		print "Lost board connection with", HOST, "port", BOARD_PORT

class ClientBoardConnFactory(ClientFactory):
	def __init__(self, gs):
		self.gs = gs
	def buildProtocol(self,addr):
		return ClientBoardConnection(self.gs)

class ClientScoreConnection(Protocol):
	def __init__(self, gs):
		self.gs = gs
	def connectionMade(self):
		print "New score connection made:", HOST, "port", SCORE_PORT
		self.sendData()
	def dataReceived(self, data): #receive other gamespace from server
		#print "Received data"
		self.gs.enemyspace.score = pickle.loads(data)
		self.sendData()
	def sendData(self):
		score = pickle.dumps(self.gs.playerspace.score) #pickle score to string
		self.transport.write(score) #send score to server
	def connectionLost(self, reason):
		print "Lost score connection with", HOST, "port", SCORE_PORT

class ClientScoreConnFactory(ClientFactory):
	def __init__(self, gs):
		self.gs = gs
	def buildProtocol(self,addr):
		return ClientScoreConnection(self.gs)


if __name__ == '__main__':
	gs = GameSpace()
	lc = LoopingCall(gs.game_loop_iterate)	
	lc.start(1/60)
	reactor.connectTCP(HOST, BOARD_PORT, ClientBoardConnFactory(gs))
	reactor.connectTCP(HOST, SCORE_PORT, ClientScoreConnFactory(gs))
	reactor.run()
