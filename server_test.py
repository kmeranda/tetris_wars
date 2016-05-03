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
PLAYER1_PORT = 40211
PLAYER2_PORT = 40311


#init queues
P1_QUEUE = DeferredQueue()
P2_QUEUE = DeferredQueue()


## player 1 ##
class Player1Connection(LineReceiver): #connects server
	def __init__(self, addr):
		self.addr = addr
	def connectionMade(self):
		print "Connection received from Player 1:", self.addr
		reactor.listenTCP(PLAYER2_PORT, Player2ConnFactory())
	def dataReceived(self, data):
		#print "Received Data:", data -- prints too much garbage
		P2_QUEUE.put(data)
		P1_QUEUE.get().addCallback(self.sendData)
	def sendData(self, data): #send data to player 1
		self.transport.write(data)
	def connectionLost(self, reason):
		print "Connection lost from Player 1:", self.addr


class Player1ConnFactory(Factory):
	def buildProtocol(self, addr): #create server
		return Player1Connection(addr)


## player 2 ##		
class Player2Connection(LineReceiver):
	def __init__(self, addr):
		self.addr = addr
	def connectionMade(self):
		print "Connection received from Player 2:", self.addr
	def dataReceived(self, data):
		#print "Received Data", data -- prints too much garbage
		P1_QUEUE.put(data)
		P2_QUEUE.get().addCallback(self.sendData)
	def sendData(self, data): #send data to player 2
		self.transport.write(data)
	def connectionLost(self, reason):
		print "Connection lost from Player 2:", self.addr


class Player2ConnFactory(Factory):
	def buildProtocol(self, addr): 
		return Player2Connection(addr)


reactor.listenTCP(PLAYER1_PORT, Player1ConnFactory())
reactor.run() #starts event loop
