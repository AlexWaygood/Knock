from __future__ import annotations

from itertools import cycle
from threading import RLock
from typing import Tuple, TYPE_CHECKING, Optional

if TYPE_CHECKING:
	from src.cards.server_card import ServerCard
	from src.special_knock_types import CardList, NumberInput


class Game:
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'StartPlay', 'RepeatGame', 'gameplayers', 'PlayerNumber', 'lock', '_StartCardNumber', 'PlayedCards', \
	            'TrumpCard', 'trumpsuit', 'Triggers'

	def __init__(self, PlayerNumber: int):
		self.StartPlay = False
		self.RepeatGame = True
		self.PlayerNumber = PlayerNumber
		self.lock = RLock()
		self._StartCardNumber = 0
		self.TrumpCard: Tuple[Optional[ServerCard]] = tuple()
		self.trumpsuit = ''
		self.PlayedCards: CardList = []

	def AddPlayerName(
			self,
			name: str,
			playerindex: int
	):

		self.gameplayers[playerindex].AddName(name)

	@property
	def StartCardNumber(self):
		return self._StartCardNumber

	@StartCardNumber.setter
	def StartCardNumber(self, number: NumberInput):
		self._StartCardNumber = int(number)

	def IncrementTriggers(self, *args: str):
		for arg in args:
			self.Triggers.Surfaces[arg] += 1

	def PlayerMakesBid(self, bid: NumberInput, playerindex: int):
		self.gameplayers[playerindex].MakeBid(int(bid))
		self.IncrementTriggers('Board')

	def ExecutePlay(
			self,
			cardID: str,
			playerindex: int
	):

		with self.lock:
			player = self.gameplayers[playerindex]
			card = player.Hand[cardID]
			player.PlayCard(card, self.trumpsuit)
			self.PlayedCards.append(card)
			self.IncrementTriggers('Board')

	def GetGameParameters(self):
		WhichRound = range(1, (self.StartCardNumber + 1))
		HowManyCards = range(self.StartCardNumber, 0, -1)
		WhoLeads = cycle(self.gameplayers)
		return WhichRound, HowManyCards, WhoLeads

	def RoundCleanUp(self):
		self.IncrementTriggers('Scoreboard', 'Board')
		self.TrumpCard = None
		self.trumpsuit = ''

	def NewGameReset(self):
		self.StartCardNumber = 0
		self.gameplayers.NewGame()
		self.IncrementTriggers('Scoreboard')
		self.StartPlay = False

	def __enter__(self):
		self.lock.acquire()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.lock.release()
		return True

	def __repr__(self):
		return f'''Object representing the current state of gameplay. Current state:
-StartPlay = {self.StartPlay}
-RepeatGame = {self.RepeatGame}
-PlayerNumber = {self.PlayerNumber}
-StartCardNumber = {self._StartCardNumber}
-TrumpCard = {self.TrumpCard!r}
-trumpsuit = {self.trumpsuit!r}
-self.PlayedCards = {[repr(card) for card in self.PlayedCards]}'''
