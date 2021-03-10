from itertools import cycle
from threading import RLock
from typing import Union


class Game(object):
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'StartPlay', 'RepeatGame', 'gameplayers', 'PlayerNumber', 'lock', '_StartCardNumber', 'PlayedCards', \
	            'TrumpCard', 'trumpsuit', 'Triggers'

	def __init__(self, PlayerNumber: int):
		self.StartPlay = False
		self.RepeatGame = True
		self.PlayerNumber = PlayerNumber
		self.lock = RLock()
		self._StartCardNumber = 0
		self.TrumpCard = None
		self.trumpsuit = ''
		self.PlayedCards = []

	def AddPlayerName(self, name, playerindex):
		"""
		@type name: str
		@type playerindex: int
		"""

		self.gameplayers[playerindex].AddName(name)

	@property
	def StartCardNumber(self):
		return self._StartCardNumber

	@StartCardNumber.setter
	def StartCardNumber(self, number: Union[int, str]):
		self._StartCardNumber = int(number)

	def IncrementTriggers(self, *args: str):
		for arg in args:
			self.Triggers.Surfaces[arg] += 1

	def PlayerMakesBid(self, bid: Union[int, str], playerindex: int):
		self.gameplayers[playerindex].MakeBid(int(bid))
		self.IncrementTriggers('Board')

	def ExecutePlay(self, cardID, playerindex):
		"""
		@type cardID: str
		@type playerindex: int
		"""

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
