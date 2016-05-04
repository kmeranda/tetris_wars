		self.winFont = pygame.font.SysFont("monospace", 50)
		self.winFont.set_bold(True)
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

