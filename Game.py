from random import shuffle
from itertools import cycle, product

from Card import Card
from Player import Player
from ServerUpdaters import AttributeTracker, Triggers

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


class Game(object):
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'RepeatGame', 'Attributes', 'GameAttributes', 'Triggers', 'StartPlay', 'gameplayers', 'GamesPlayed', \
	            'PlayerNumber', 'Sendable'

	def __init__(self, PlayerNumber):
		self.StartPlay = False
		self.RepeatGame = True
		self.Attributes = AttributeTracker()
		self.Triggers = Triggers()
		self.gameplayers = Player.AllPlayers
		self.gameplayers.PlayerNo = PlayerNumber
		self.GamesPlayed = 0
		self.PlayerNumber = PlayerNumber
		self.Sendable = True

	# A few functions to be accessed by the threaded-client function.

	def AddPlayerName(self, name, playerindex):
		self.gameplayers[playerindex].name = name

	def TimeToStart(self):
		self.StartPlay = True

	def PlayerActionCompleted(self, playerindex):
		self.gameplayers[playerindex].ActionComplete = True

	def SetCardNumber(self, number):
		self.Attributes.StartCardNumber = int(number)

	def PlayerMakesBid(self, bid, playerindex=-1, player=None):
		"""This method is designed to be used by the server or the client"""
		player = player if player else self.gameplayers[playerindex]
		player.MakeBid(int(bid))
		self.IncrementTriggers('Board')

	def ExecutePlay(self, cardID, playerindex):
		"""This method is designed to be used by the server or the client"""
		self.Sendable = False
		player = self.gameplayers[playerindex]
		player.PlayCard((card := next(card for card in player.Hand if card.ID == cardID)), self.Attributes.trumpsuit)
		self.Attributes.PlayedCards.append(card)
		self.IncrementTriggers('Board')
		self.Sendable = True

	def RepeatQuestionAnswer(self):
		self.RepeatGame = True

	# The remaining functions relate to the order of gameplay.
	# All are used only on the server sie, except where specified.

	def IncrementTriggers(self, *args):
		for arg in args:
			self.Triggers.Surfaces[arg] += 1

	def WaitForPlayers(self, attribute):
		self.Triggers.Events[attribute] += 1
		self.gameplayers.WaitForPlayers()

	def GetGameParameters(self):
		"""Can be used on either the client side or the server side"""

		WhichRound = range(1, (self.Attributes.StartCardNumber + 1))
		HowManyCards = range(self.Attributes.StartCardNumber, 0, -1)
		WhoLeads = cycle(self.gameplayers)
		return WhichRound, HowManyCards, WhoLeads

	def RoundCleanUp(self, gameplayers, server=False):
		"""Can be used on either the client or the server side"""

		self.Sendable = False
		gameplayers.RoundCleanUp(server)
		self.IncrementTriggers('Scoreboard', 'Board')
		self.Attributes.TrumpCard = None
		self.Attributes.trumpsuit = ''
		self.Sendable = True

	def GameCleanUp(self):
		"""To be used on client-side only"""
		self.Sendable = False
		self.gameplayers.GameCleanUp()
		self.IncrementTriggers('Scoreboard')
		self.Sendable = True

	def NewGameReset(self):
		self.Sendable = False
		self.Attributes.StartCardNumber = 0
		self.gameplayers.NewGame()
		self.IncrementTriggers('Scoreboard')
		self.StartPlay = False
		self.Sendable = True

	def PlayGame(self):
		# Wait until the opening sequence is complete

		while not self.Attributes.StartCardNumber:
			delay(1)

		self.gameplayers.NextStage()
		self.WaitForPlayers('GameInitialisation')
		self.Triggers.Events['StartNumberSet'] += 1

		for cardnumber in range(self.Attributes.StartCardNumber, 0, -1):
			self.PlayRound(cardnumber)

		self.RepeatGame = False

		while not self.RepeatGame:
			delay(1)

		self.NewGameReset()

		# Wait until all players have logged their new playerindex.
		self.WaitForPlayers('NewGameReset')

	def PlayRound(self, cardnumber):
		# Make a new pack of cards, set the trumpsuit.
		Pack = [Card(*prod) for prod in product(range(2, 15), ('D', 'S', 'C', 'H'))]
		shuffle(Pack)
		self.Sendable = False
		self.Attributes.TrumpCard = (TrumpCard := Pack.pop())
		self.Attributes.trumpsuit = (trumpsuit := TrumpCard.ActualSuit)
		self.Triggers.Events['NewPack'] += 1
		self.Sendable = True

		# Deal cards
		self.Sendable = False
		self.gameplayers.ReceiveCards(Pack, cardnumber, trumpsuit)
		self.IncrementTriggers('TrumpCard', 'Board', 'Scoreboard')
		self.Sendable = True
		self.WaitForPlayers('CardsDealt')

		# Play tricks
		for i in range(cardnumber):
			self.PlayTrick()

		# Award points, reset players for the next round.
		self.RoundCleanUp(self.gameplayers, True)

	def PlayTrick(self):
		self.WaitForPlayers('TrickStart')

		for i in range(self.PlayerNumber):
			self.IncrementTriggers('Board')
			while len(self.Attributes.PlayedCards) == i:
				delay(1)

		self.gameplayers.NextStage()
		self.WaitForPlayers('TrickWinnerLogged')
		self.Attributes.PlayedCards.clear()
		self.IncrementTriggers('Board')
		self.WaitForPlayers('TrickEnd')

	def __eq__(self, other):
		return all((
			self.Triggers == other.Triggers,
			self.gameplayers == other.gameplayers,
			self.StartPlay == other.StartPlay,
			self.RepeatGame == other.RepeatGame,
			self.GamesPlayed == other.GamesPlayed,
			self.PlayerNumber == other.PlayerNumber
		))
