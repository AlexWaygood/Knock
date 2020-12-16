"""Class for encoding order of gameplay, in coordination with the client script."""

from random import shuffle
from itertools import chain, cycle
from Card import Card
from Player import Player

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


class Game(object):
	__slots__ = 'StartCardPositions', 'CardPositions', 'RepeatGame', 'TournamentAttributes', 'GameAttributes', \
	            'RoundAttributes', 'TrickAttributes', 'ClientTriggers', 'SurfaceIterations', 'StartPlay'

	def __init__(self, NumberOfPlayers):
		self.StartCardPositions = [i for i in range(NumberOfPlayers)]
		self.CardPositions = self.StartCardPositions
		self.StartPlay = False
		self.RepeatGame = True

		self.TournamentAttributes = {
			'GamesPlayed': 0,
			'TournamentLeaders': [],
			'MaxGamesWon': 0,
			'NumberOfPlayers': NumberOfPlayers,
			'MaxCardNumber': min(13, (51 // NumberOfPlayers)),
			'gameplayers': Player.AllPlayers
		}

		self.GameAttributes = {
			'StartCardNumber': 0,
			'Winners': [],
			'MaxPoints': 0
		}

		self.RoundAttributes = {
			'RoundNumber': 1,
			'PackOfCards': [],
			'CardNumberThisRound': 0,
			'TrumpCard': None,
			'trumpsuit': '',
			'RoundLeader': None
		}

		self.TrickAttributes = {
			'PlayedCards': [],
			'FirstPlayerIndex': 0,
			'TrickNumber': 0,
			'Winner': None,
			'WhoseTurnPlayerIndex': -1,
			'TrickInProgress': False
		}

		self.ClientTriggers = {
			'GameInitialisation': 0,
			'RoundStart': 0,
			'NewPack': 0,
			'CardsDealt': 0,
			'TrickStart': 0,
			'TrickEnd': 0,
			'RoundEnd': 0,
			'PointsAwarded': 0,
			'WinnersAnnounced': 0,
			'TournamentLeaders': 0,
			'NewGameReset': 0
		}

		self.SurfaceIterations = {
			'Scoreboard': 1,
			'CurrentBoard': 1,
			'TrumpCard': 0
		}

	# A few functions to be accessed by the threaded-client function.

	def AddPlayerName(self, name, playerindex):
		Player.AllPlayers[playerindex].AddName(name)

	def TimeToStart(self):
		self.StartPlay = True

	def PlayerActionCompleted(self, playerindex):
		Player.AllPlayers[playerindex].ActionComplete = True

	def SetCardNumber(self, number):
		self.GameAttributes['StartCardNumber'] = int(number)

	def PlayerMakesBid(self, playerindex, bid):
		Player.AllPlayers[playerindex].MakeBid(int(bid))
		self.SurfaceIterations['CurrentBoard'] += 1

	def ExecutePlay(self, cardID, playerindex):
		player = Player.AllPlayers[playerindex]
		card = next(card for card in player.Hand if card.ID == cardID)
		player.PlayCard(card, self.RoundAttributes['trumpsuit'])
		card.SetPos(self.CardPositions[len(self.TrickAttributes['PlayedCards'])])
		self.TrickAttributes['PlayedCards'].append(card)
		self.SurfaceIterations['CurrentBoard'] += 1

	def RepeatQuestionAnswer(self):
		self.RepeatGame = True

	# The remaining functions relate to the order of gameplay.

	def WaitForPlayers(self, attribute):
		self.ClientTriggers[attribute] += 1

		while any(not player.ActionComplete for player in Player.AllPlayers):
			delay(60)

		Player.AllPlayers = [player.NextStage() for player in Player.AllPlayers]

	def PlayGame(self):
		# Wait until the opening sequence is complete
		self.WaitForPlayers('GameInitialisation')

		WhichRound = range(1, (self.GameAttributes['StartCardNumber'] + 1))
		HowManyCards = range(self.GameAttributes['StartCardNumber'], 0, -1)
		WhoLeads = cycle(Player.AllPlayers)

		for roundnumber, cardnumber, RoundLeader in zip(WhichRound, HowManyCards, WhoLeads):
			self.PlayRound(roundnumber, cardnumber, RoundLeader)

		self.GameAttributes['MaxPoints'] = max(player.Points for player in Player.AllPlayers)

		self.GameAttributes['Winners'] = [
			player for player in Player.AllPlayers
			if player.Points == self.GameAttributes['MaxPoints']
		]

		for player in self.GameAttributes['Winners']:
			player.GamesWon += 1

		self.SurfaceIterations['Scoreboard'] += 1

		# Wait until all players have finished announcing the game winners.
		self.WaitForPlayers('WinnersAnnounced')

		if self.TournamentAttributes['GamesPlayed']:
			self.TournamentAttributes['MaxGamesWon'] = max(player.GamesWon for player in Player.AllPlayers)

			self.TournamentAttributes['TournamentLeaders'] = [
				player for player in Player.AllPlayers
				if player.GamesWon == self.TournamentAttributes['MaxGamesWon']
			]

			self.ClientTriggers['TournamentLeaders'] += 1

		self.RepeatGame = False

		while not self.RepeatGame:
			delay(1)

		self.NewGameReset()

		# Wait until all players have logged their new playerindex.
		self.WaitForPlayers('NewGameReset')

		self.PlayGame()

	def PlayRound(self, roundnumber, cardnumber, RoundLeader):
		self.RoundAttributes['CardNumberThisRound'] = cardnumber
		self.RoundAttributes['RoundNumber'] = roundnumber
		self.RoundAttributes['RoundLeader'] = RoundLeader
		RoundLeader.RoundLeader = True
		self.SurfaceIterations['Scoreboard'] += 1

		self.WaitForPlayers('RoundStart')

		# the trumpcard is set as part of this function call.
		self.NewPack()
		self.WaitForPlayers('NewPack')

		# Deal cards
		Pack, trumsuit = self.RoundAttributes['PackOfCards'], self.RoundAttributes['trumpsuit']

		Player.AllPlayers = [
			player.ReceiveCards([Pack.pop() for i in range(cardnumber)], trumsuit)
			for player in Player.AllPlayers
		]

		self.SurfaceIterations['TrumpCard'] += 1
		self.SurfaceIterations['CurrentBoard'] += 1
		self.WaitForPlayers('CardsDealt')

		FirstPlayer = RoundLeader
		RoundLeader.RoundLeader = False

		for i in range(cardnumber):
			FirstPlayerIndex = self.TrickStart(i + 1, FirstPlayer)
			self.TrickMiddle(FirstPlayerIndex)
			FirstPlayer = self.TrickEnd(self.TrickAttributes['PlayedCards'])

		self.WaitForPlayers('RoundEnd')

		Player.AllPlayers = [player.ReceivePoints() for player in Player.AllPlayers]

		self.SurfaceIterations['Scoreboard'] += 1
		self.WaitForPlayers('PointsAwarded')

		Player.AllPlayers = [player.EndOfRound() for player in Player.AllPlayers]

		self.RoundAttributes['TrumpCard'] = None
		self.RoundAttributes['trumpsuit'] = ''

		if self.RoundAttributes['RoundNumber'] != self.GameAttributes['StartCardNumber']:
			self.RoundAttributes['RoundNumber'] += 1
			self.RoundAttributes['CardNumberThisRound'] -= 1
			self.TrickAttributes['TrickNumber'] = 1

		self.SurfaceIterations['CurrentBoard'] += 1
		self.SurfaceIterations['Scoreboard'] += 1

	def NewPack(self):
		PackOfCards = [Card(value, suit) for value in range(2, 15) for suit in ('D', 'S', 'C', 'H')]
		shuffle(PackOfCards)
		TrumpCard = PackOfCards.pop()

		self.RoundAttributes['trumpsuit'] = TrumpCard.ActualSuit
		self.RoundAttributes['PackOfCards'] = PackOfCards
		self.RoundAttributes['TrumpCard'] = TrumpCard
		self.SurfaceIterations['TrumpCard'] += 1

	def TrickStart(self, TrickNumber, FirstPlayer):
		self.TrickAttributes['TrickInProgress'] = True
		self.TrickAttributes['TrickNumber'] = TrickNumber

		FirstPlayerIndex = FirstPlayer.playerindex
		self.TrickAttributes['FirstPlayerIndex'] = FirstPlayerIndex

		self.CardPositions = (self.StartCardPositions[FirstPlayerIndex:]
		                      + self.StartCardPositions[:FirstPlayerIndex])
		return FirstPlayerIndex

	def TrickMiddle(self, FirstPlayerIndex):
		self.WaitForPlayers('TrickStart')

		for i in chain(range(FirstPlayerIndex, self.TournamentAttributes['NumberOfPlayers']), range(FirstPlayerIndex)):

			currentnumber = len(self.TrickAttributes['PlayedCards'])
			self.TrickAttributes['WhoseTurnPlayerIndex'] = i
			self.SurfaceIterations['CurrentBoard'] += 1

			while len(self.TrickAttributes['PlayedCards']) == currentnumber:
				delay(60)

	def TrickEnd(self, PlayedCards):
		self.TrickAttributes['WhoseTurnPlayerIndex'] = -1
		self.TrickAttributes['TrickInProgress'] = False
		self.TrickAttributes['Winner'] = (
			max((card.DetermineWinValue(PlayedCards[0].ActualSuit, self.RoundAttributes['trumpsuit'])
			     for card in PlayedCards), key=Card.GetWinValue)).PlayedBy

		self.TrickAttributes['Winner'].WinsTrick()
		self.TrickAttributes['FirstPlayerIndex'] = 0

		delay(500)

		PlayedCards.clear()
		self.SurfaceIterations['CurrentBoard'] += 1

		self.WaitForPlayers('TrickEnd')
		return self.TrickAttributes['Winner']

	def NewGameReset(self):
		self.GameAttributes['StartCardNumber'] = 0
		self.RoundAttributes['RoundNumber'] = 1

		Player.AllPlayers = (Player.AllPlayers[1:] + Player.AllPlayers[:1])
		Player.AllPlayers = [player.ResetPlayer(Player.AllPlayers.index(player)) for player in Player.AllPlayers]

		self.TournamentAttributes['GamesPlayed'] += 1
		self.SurfaceIterations['Scoreboard'] += 1
		self.StartPlay = False
