# tetris_wars
# server


import os
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol
from twisted.protocols.basic import LineReceiver
from twisted.internet.tcp import Port
from twisted.internet import reactor
from twisted.internet.defer import DeferredQueue


#init port number
PLAYER1_BOARDPORT = 40011
PLAYER2_BOARDPORT = 40111
PLAYER1_SCOREPORT = 40211
PLAYER2_SCOREPORT = 40311


#init queues
P1_BOARDQUEUE = DeferredQueue()
P2_BOARDQUEUE = DeferredQueue()
P1_PIECEQUEUE = DeferredQueue()
P2_PIECEQUEUE = DeferredQueue()
P1_SCOREQUEUE = DeferredQueue()
P2_SCOREQUEUE = DeferredQueue()


## player 1 ##
class P1BoardConnection(LineReceiver): #connects server
	def __init__(self, addr):
		self.addr = addr
	def connectionMade(self):
		print "Board connection received from Player 1:", self.addr
		reactor.listenTCP(PLAYER2_BOARDPORT, P2BoardConnFactory())
	def dataReceived(self, data):
		#print "Received Data:", data -- prints too much garbage
		P2_BOARDQUEUE.put(data)
		P1_BOARDQUEUE.get().addCallback(self.sendData)
	def sendData(self, data): #send data to player 1
		self.transport.write(data)
	def connectionLost(self, reason):
		print "Board connection lost from Player 1:", self.addr

class P1BoardConnFactory(Factory):
	def buildProtocol(self, addr): #create server
		return P1BoardConnection(addr)

class P1ScoreConnection(LineReceiver): #connects server
	def __init__(self, addr):
		self.addr = addr
	def connectionMade(self):
		print "Score connection received from Player 1:", self.addr
		reactor.listenTCP(PLAYER2_SCOREPORT, P2ScoreConnFactory())
	def dataReceived(self, data):
		#print "Received Data:", data
		P2_SCOREQUEUE.put(data)
		P1_SCOREQUEUE.get().addCallback(self.sendData)
	def sendData(self, data): #send data to player 1
		self.transport.write(data)
	def connectionLost(self, reason):
		print "Score connection lost from Player 1:", self.addr

class P1ScoreConnFactory(Factory):
	def buildProtocol(self, addr): #create server
		return P1ScoreConnection(addr)

## player 2 ##		
class P2BoardConnection(LineReceiver):
	def __init__(self, addr):
		self.addr = addr
	def connectionMade(self):
		print "Board connection received from Player 2:", self.addr
	def dataReceived(self, data):
		#print "Received Data", data -- prints too much garbage
		P1_BOARDQUEUE.put(data)
		P2_BOARDQUEUE.get().addCallback(self.sendData)
	def sendData(self, data): #send data to player 2
		self.transport.write(data)
	def connectionLost(self, reason):
		print "Board connection lost from Player 2:", self.addr

class P2BoardConnFactory(Factory):
	def buildProtocol(self, addr): 
		return P2BoardConnection(addr)

class P2ScoreConnection(LineReceiver):
	def __init__(self, addr):
		self.addr = addr
	def connectionMade(self):
		print "Score connection received from Player 2:", self.addr
	def dataReceived(self, data):
		#print "Received Data", data
		P1_SCOREQUEUE.put(data)
		P2_SCOREQUEUE.get().addCallback(self.sendData)
	def sendData(self, data): #send data to player 2
		self.transport.write(data)
	def connectionLost(self, reason):
		print "Score connection lost from Player 2:", self.addr

class P2ScoreConnFactory(Factory):
	def buildProtocol(self, addr): 
		return P2ScoreConnection(addr)


reactor.listenTCP(PLAYER1_BOARDPORT, P1BoardConnFactory())
reactor.listenTCP(PLAYER1_SCOREPORT, P1ScoreConnFactory())
reactor.run() #starts event loop
