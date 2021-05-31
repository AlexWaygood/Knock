from __future__ import annotations

from typing import TYPE_CHECKING
from src.players.players_abstract import Player

if TYPE_CHECKING:
	import src.special_knock_types as skt


class Game:
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'StartPlay', 'RepeatGame', 'PlayerNumber', '_StartCardNumber', 'PlayedCards', 'TrumpCard', 'trumpsuit',\
	            'Triggers', 'BiddingSystem'

	def __init__(self, BiddingSystem: str) -> None:
		# The PlayerNumber is set as an instance variable on the server side but a class variable on the client side.
		# So we don't bother with it here.

		self.StartPlay = False
		self.RepeatGame = True
		self._StartCardNumber = 0
		self.TrumpCard: skt.OptionalTrump = tuple()
		self.trumpsuit: skt.OptionalSuit = None
		self.PlayedCards: skt.AnyCardList = []
		self.BiddingSystem = BiddingSystem

	@property
	def StartCardNumber(self) -> int:
		return self._StartCardNumber

	@StartCardNumber.setter
	def StartCardNumber(self, number: skt.NumberInput) -> None:
		self._StartCardNumber = int(number)

	def ExecutePlay(
			self,
			cardID: str,
			playerindex: int
	) -> None:

		player = Player.player(playerindex)
		card = player.Hand[cardID]
		player.PlayCard(card, self.trumpsuit)
		self.PlayedCards.append(card)

	def GetGameParameters(self) -> skt.GameParameters:
		WhichRound = range(1, (self.StartCardNumber + 1))
		HowManyCards = range(self.StartCardNumber, 0, -1)
		WhoLeads = Player.cycle()
		return WhichRound, HowManyCards, WhoLeads

	def RoundCleanUp(self) -> None:
		self.TrumpCard = None
		self.trumpsuit = None

	def NewGameReset(self) -> None:
		self.StartCardNumber = 0
		Player.NewGame()
		self.StartPlay = False

	def __repr__(self) -> str:
		return f'''Object representing the current state of gameplay. Current state:
-StartPlay = {self.StartPlay}
-RepeatGame = {self.RepeatGame}
-PlayerNumber = {self.PlayerNumber}
-StartCardNumber = {self._StartCardNumber}
-TrumpCard = {self.TrumpCard!r}
-trumpsuit = {self.trumpsuit!r}
-self.PlayedCards = {[repr(card) for card in self.PlayedCards]}'''


def EventsDict() -> skt.EventsDictType:
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
