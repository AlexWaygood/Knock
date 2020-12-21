from random import shuffle
from itertools import chain, cycle

from Card import Card
from ClientClasses import *

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


class Game(object):
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'StartCardPositions', 'CardPositions', 'RepeatGame', 'Attributes', 'GameAttributes', 'Triggers', \
	            'StartPlay'

	def __init__(self, PlayerNumber):
		self.StartCardPositions = [i for i in range(PlayerNumber)]
		self.CardPositions = self.StartCardPositions
		self.StartPlay = False
		self.RepeatGame = True
		self.Attributes = AttributeTracker(True, PlayerNumber)
		self.Triggers = Triggers()

	# A few functions to be accessed by the threaded-client function.

	@staticmethod
	def AddPlayerName(name, playerindex):
		Player.AllPlayers[playerindex].AddName(name)

	def TimeToStart(self):
		self.StartPlay = True

	@staticmethod
	def PlayerActionCompleted(playerindex):
		Player.AllPlayers[playerindex].ActionComplete = True

	def SetCardNumber(self, number):
		self.Attributes.StartCardNumber = int(number)

	def PlayerMakesBid(self, bid, playerindex=-1, player=None):
		"""This method is designed to be used by the server or the client"""
		player = player if player else Player.AllPlayers[playerindex]
		player.MakeBid(int(bid))
		self.Triggers.Surfaces['CurrentBoard'] += 1

	def ExecutePlay(self, cardID='', playerindex=-1, card=None, player=None):
		"""This method is designed to be used by the server or the client"""

		if not player:
			player = Player.AllPlayers[playerindex]
			card = next(card for card in player.Hand if card.ID == cardID)

		player.PlayCard(card, self.Attributes.Round['trumpsuit'])
		card.SetPos(self.CardPositions[len(self.Attributes.Trick['PlayedCards'])])
		self.Attributes.Trick['PlayedCards'].append(card)
		self.Triggers.Surfaces['CurrentBoard'] += 1

	def RepeatQuestionAnswer(self):
		self.RepeatGame = True

	# The remaining functions relate to the order of gameplay.
	# All are used only on the server sie, except where specified.

	def WaitForPlayers(self, attribute):
		self.Triggers.Events[attribute] += 1

		while any(not player.ActionComplete for player in Player.AllPlayers):
			delay(60)

		Player.AllPlayers = [player.NextStage() for player in Player.AllPlayers]

	def GetGameParameters(self):
		"""Can be used on either the client side or the server side"""

		WhichRound = range(1, (self.Attributes.StartCardNumber + 1))
		HowManyCards = range(self.Attributes.StartCardNumber, 0, -1)
		WhoLeads = cycle(self.Attributes.Tournament['gameplayers'])
		return WhichRound, HowManyCards, WhoLeads

	def TrickCleanUp(self, PlayedCards):
		"""This is to be used on the client side as well as the server side."""

		self.Attributes.Trick.update({
			'WhoseTurnPlayerIndex': -1,
			'TrickInProgress': False,

			'Winner': (
				max((card.DetermineWinValue(PlayedCards[0].ActualSuit, self.Attributes.Round['trumpsuit'])
				     for card in PlayedCards), key=Card.GetWinValue)).PlayedBy,

			'FirstPlayerIndex': -1
		})

		self.Attributes.Trick['Winner'].WinsTrick()

	def RoundCleanUp(self):
		"""Can be used on either the client or the server side"""

		players = [player.EndOfRound() for player in self.Attributes.Tournament['gameplayers']]
		self.Triggers.Surfaces['Scoreboard'] += 1

		self.Attributes.Round.update({
			'TrumpCard': None,
			'trumpsuit': ''
		})

		if self.Attributes.Round['RoundNumber'] != self.Attributes.StartCardNumber:
			self.Attributes.Round['RoundNumber'] += 1
			self.Attributes.Round['CardNumberThisRound'] -= 1
			self.Attributes.Trick['TrickNumber'] = 1

		self.Triggers.Surfaces['CurrentBoard'] += 1
		self.Triggers.Surfaces['Scoreboard'] += 1

	def GameCleanUp(self, GamesPlayed):
		"""To be used on both client and server sides"""

		players = self.Attributes.Tournament['gameplayers']
		MaxPoints = max(player.Points for player in players)
		Winners = [player.WinsGame() for player in players if player.Points == MaxPoints]
		self.Triggers.Surfaces['Scoreboard'] += 1

		if GamesPlayed:
			MaxGamesWon = self.Attributes.Tournament['MaxGamesWon'] = max(player.GamesWon for player in players)
			TournamentLeaders = [player for player in players if player.GamesWon == MaxGamesWon]
			self.Attributes.Tournament['TournamentLeaders'] = TournamentLeaders
		else:
			MaxGamesWon = 0
			TournamentLeaders = []

		return Winners, MaxPoints, TournamentLeaders, MaxGamesWon

	def NewGameReset(self):
		self.Attributes.StartCardNumber = 0
		self.Attributes.Round['RoundNumber'] = 1

		Player.AllPlayers = Player.AllPlayers[1:] + Player.AllPlayers[:1]
		Player.AllPlayers = [player.ResetPlayer(Player.AllPlayers.index(player)) for player in Player.AllPlayers]
		self.Attributes.Tournament['gameplayers'] = Player.AllPlayers

		self.Triggers.Surfaces['Scoreboard'] += 1
		self.StartPlay = False

	def PlayGame(self, GamesPlayed):
		# Wait until the opening sequence is complete
		self.WaitForPlayers('GameInitialisation')
		self.Triggers.Events['StartNumberSet'] += 1

		for roundnumber, cardnumber, RoundLeader in zip(*self.GetGameParameters()):
			self.PlayRound(cardnumber, RoundLeader.playerindex)

		self.GameCleanUp(GamesPlayed)
		self.RepeatGame = False

		while not self.RepeatGame:
			delay(1)

		self.NewGameReset()

		# Wait until all players have logged their new playerindex.
		self.WaitForPlayers('NewGameReset')

	def PlayRound(self, cardnumber, FirstPlayerIndex):
		self.Triggers.Surfaces['Scoreboard'] += 1

		# Make a new pack of cards, set the trumpsuit.
		Pack = [Card(value, suit) for value in range(2, 15) for suit in ('D', 'S', 'C', 'H')]
		shuffle(Pack)

		self.Attributes.Round.update({
			'TrumpCard': (TrumpCard := Pack.pop()),
			'trumpsuit': (trumpsuit := TrumpCard.ActualSuit),
			'PackOfCards': Pack,

		})

		self.Triggers.Surfaces['TrumpCard'] += 1
		self.Triggers.Events['NewPack'] += 1

		# Deal cards
		players = Player.AllPlayers
		players = [player.ReceiveCards([Pack.pop() for i in range(cardnumber)], trumpsuit) for player in players]

		self.Triggers.Surfaces['TrumpCard'] += 1
		self.Triggers.Surfaces['CurrentBoard'] += 1

		self.WaitForPlayers('CardsDealt')

		# Play tricks
		for i in range(cardnumber):
			FirstPlayerIndex = self.PlayTrick((i + 1), FirstPlayerIndex)

		# Award points, reset players for the next round.
		self.RoundCleanUp()

	def PlayTrick(self, TrickNumber, FirstPlayerIndex):
		self.Attributes.Trick.update({
			'TrickInProgress': True,
			'TrickNumber': TrickNumber
		})

		self.CardPositions = self.StartCardPositions[FirstPlayerIndex:] + self.StartCardPositions[:FirstPlayerIndex]

		PlayerNo = self.Attributes.Tournament['PlayerNumber']
		PlayerOrder = enumerate(chain(range(FirstPlayerIndex, PlayerNo), range(FirstPlayerIndex)))
		self.WaitForPlayers('TrickStart')

		for CardNumberOnBoard, WhoseTurn in PlayerOrder:
			self.Attributes.Trick['WhoseTurnPlayerIndex'] = WhoseTurn
			self.Triggers.Surfaces['CurrentBoard'] += 1
			while len(self.Attributes.Trick['PlayedCards']) == CardNumberOnBoard:
				delay(1)

		self.TrickCleanUp(self.Attributes.Trick['PlayedCards'])

		# This can happen immediately on the server side, but happens after a delay on the client side.
		# The TrickCleanUp method is to be used on both sides.
		self.Attributes.Trick['PlayedCards'].clear()

		self.Triggers.Surfaces['CurrentBoard'] += 1
		self.WaitForPlayers('TrickEnd')
		return self.Attributes.Trick['Winner'].playerindex
