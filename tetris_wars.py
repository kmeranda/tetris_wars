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
		self.titleFont = pygame.font.SysFont("monospace", 50)
		self.title = self.titleFont.render("Tetris Wars", 1, (255,255,255))
		self.playerFont = pygame.font.SysFont("monospace", 30)
		self.playerHeader = self.playerFont.render("Player 1", 1, (255,255,255))
		self.playerBoardCaption = self.playerFont.render("Player's Board", 1, (255,255,255))
		self.opponentBoardCaption = self.playerFont.render("Opponent's Board", 1, (255,255,255))
		self.scoreCaption = self.playerFont.render("Score: ", 1, (255,255,255))
		self.winFont = pygame.font.SysFont("monospace", 50)
		self.winFont.set_bold(True)
		
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
		for i in range(0, len(self.enemyspace.board.images)):
			self.screen.blit(self.enemyspace.board.borders[i], self.enemyspace.board.borderRects[i])
			self.screen.blit(self.enemyspace.board.images[i], self.enemyspace.board.rects[i])
		for i in range(4):
			self.screen.blit(self.playerspace.curr_piece.borders[i], self.playerspace.curr_piece.borderRects[i])
			self.screen.blit(self.playerspace.curr_piece.images[i], self.playerspace.curr_piece.rects[i])
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
			elif self.enemyspace.score > self.playerspace.score: #opp has higher score
				self.winText = 'YOU LOSE.'
			else: #draw
				self.winText = "IT'S A TIE."
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
		self.curr_piece = CurrentPiece(self)
		self.score = 0
		self.state = 0 #playing=0, gameover=1
	def move(self, dir):
		for i in range(4):
			self.curr_piece.xpos[i] += dir
		if self.collision(self.board.boardArray, self.curr_piece):
			for i in range(4):
				self.curr_piece.xpos[i] -= dir

	def place(self):
		# curr_piece tick logic looped until it hits the bottom
		while not self.collision(self.board.boardArray, self.curr_piece):
			self.curr_piece.tick()
		self.curr_piece.untick()
		for i in range(4):
			x = self.curr_piece.xpos[i]
			y = self.curr_piece.ypos[i]
			s = self.curr_piece.shape
			try:
				self.board.boardArray[y][x] = s
			except:
				pass
		self.curr_piece = CurrentPiece(self)	# re-init curr_piece
		if self.collision(self.board.boardArray, self.curr_piece):
			self.state = 1
			self.board.boardArray[self.board.height-1][self.board.width-1] = 1
			self.curr_piece.untick()
	
	def rotate(self):
		if self.curr_piece.shape != 'O':	# cannot rotate square
			x_arr = [self.curr_piece.xpos[i] for i in range(4)]
			y_arr = [self.curr_piece.ypos[i] for i in range(4)]
			x = x_arr[2]	# rotate about 3rd square
			y = y_arr[2]
			# get distances from 
			x_dist = [(x_arr[i]-x) for i in range(4)]
			y_dist = [(y_arr[i]-y) for i in range(4)]
			self.curr_piece.xpos = [(x-y_dist[i]) for i in range(4)]
			self.curr_piece.ypos = [(y+x_dist[i]) for i in range(4)]
			if self.collision(self.board.boardArray, self.curr_piece): # rotate causes problems
				self.curr_piece.xpos = x_arr
				self.curr_piece.ypos = y_arr

	def collision(self, board, piece):
		num = 0
		for i in range(4):
			if piece.ypos[i]<0:	# collision with bottom
				return True
			if piece.xpos[i]<0 or piece.xpos[i]>len(board[i])-1: # collision with sides
				return True
			if piece.ypos[i]<len(board):	# only an issue for end game
				if board[piece.ypos[i]][piece.xpos[i]]!=0:	# collision with other piece
					return True
		return False
		
	def tick(self):
		self.board.createSquares() #visually interpret board
		self.score += self.board.moveDown() # delete full rows in board and increase score
		self.state = self.board.boardArray[self.board.height-1][self.board.width-1]
		#update current piece only on own board
		if self.num == 1 and self.state != 1:	# piece logic only on player and only when not lost
			# curr_piece tick logic
			self.curr_piece.tick()
			self.piece_landed = self.collision(self.board.boardArray, self.curr_piece)
			if self.piece_landed:	# add curr_piece to boardArray
				self.curr_piece.untick()
				for i in range(4):
					x = self.curr_piece.xpos[i]
					y = self.curr_piece.ypos[i]
					s = self.curr_piece.shape
					try:
						self.board.boardArray[y][x] = s
					except:
						pass
				self.curr_piece = CurrentPiece(self)	# re-init curr_piece
				while self.collision(self.board.boardArray, self.curr_piece):
					self.state = 1
					self.board.boardArray[self.board.height-1][self.board.width-1] = 1
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
		self.images = []
		self.rects = []
		self.borders = []
		self.borderRects = []
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
				if (self.boardArray[y][x] not in [0,1]): #create square, rect, and border for all filled coordinates
					self.centerx = self.start_xCoord+13+(26*x)
					self.centery = 73+(26*(self.height-(y+1)))
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
	def moveDown(self):
		updateScore = 0
		for y in range(self.height):	# iterate through rows in board
			if not 0 in self.boardArray[y]:	# check for no empty space in row
				del self.boardArray[y]	# delete full row
				self.boardArray.append([0 for x in range(self.width)]) # add empty row to top
				updateScore += 1
		return updateScore


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

			self.centerx = 23+(26*self.xpos[x])
			self.centery = 73+(26*(20-(self.ypos[x]+1)))
			self.squareImage = pygame.Surface((24,24))
			self.squareImage.fill(self.squareColor)
			if self.ypos[x]>19:	# end pieces
				self.squareImage.fill((0,0,0))
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
			array[self.gs.playerspace.curr_piece.ypos[i]][self.gs.playerspace.curr_piece.xpos[i]] = self.gs.playerspace.curr_piece.shape
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
		#print self.gs.enemyspace.score
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
