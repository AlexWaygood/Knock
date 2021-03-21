from __future__ import annotations

from itertools import cycle
from typing import TYPE_CHECKING
from src.players.players_abstract import Player

if TYPE_CHECKING:
	from src.special_knock_types import CardList, NumberInput, OptionalTrump, OptionalSuit


class Game:
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'StartPlay', 'RepeatGame', 'PlayerNumber', '_StartCardNumber', 'PlayedCards', 'TrumpCard', 'trumpsuit',\
	            'Triggers'

	def __init__(self):
		# The PlayerNumber is set as an instance variable on the server side but a class variable on the client side.
		# So we don't bother with it here.

		self.StartPlay = False
		self.RepeatGame = True
		self._StartCardNumber = 0
		self.TrumpCard: OptionalTrump = tuple()
		self.trumpsuit: OptionalSuit = None
		self.PlayedCards: CardList = []

	@property
	def StartCardNumber(self):
		return self._StartCardNumber

	@StartCardNumber.setter
	def StartCardNumber(self, number: NumberInput):
		self._StartCardNumber = int(number)

	def ExecutePlay(
			self,
			cardID: str,
			playerindex: int
	):

		player = Player.AllPlayers[playerindex]
		card = player.Hand[cardID]
		player.PlayCard(card, self.trumpsuit)
		self.PlayedCards.append(card)

	def GetGameParameters(self):
		WhichRound = range(1, (self.StartCardNumber + 1))
		HowManyCards = range(self.StartCardNumber, 0, -1)
		WhoLeads = cycle(Player.AllPlayers)
		return WhichRound, HowManyCards, WhoLeads

	def RoundCleanUp(self):
		self.TrumpCard = None
		self.trumpsuit = ''

	def NewGameReset(self):
		self.StartCardNumber = 0
		Player.NewGame()
		self.StartPlay = False

	def __repr__(self):
		return f'''Object representing the current state of gameplay. Current state:
-StartPlay = {self.StartPlay}
-RepeatGame = {self.RepeatGame}
-PlayerNumber = {self.PlayerNumber}
-StartCardNumber = {self._StartCardNumber}
-TrumpCard = {self.TrumpCard!r}
-trumpsuit = {self.trumpsuit!r}
-self.PlayedCards = {[repr(card) for card in self.PlayedCards]}'''


def EventsDict():
	return {
		'GameInitialisation': 0,
		'RoundStart': 0,
		'NewPack': 0,
		'CardsDealt': 0,
		'TrickStart': 0,
		'TrickWinnerLogged': 0,
		'TrickEnd': 0,
		'RoundEnd': 0,
		'PointsAwarded': 0,
		'WinnersAnnounced': 0,
		'TournamentLeaders': 0,
		'NewGameReset': 0,
		'StartNumberSet': 0
	}
