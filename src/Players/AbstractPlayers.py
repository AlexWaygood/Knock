from typing import Union
from src.Players.Hand import Hand
from collections import UserList


class Gameplayers(UserList):
	__slots__ = 'PlayerNo', 'Dict'

	def __init__(self):
		super().__init__()
		self.PlayerNo = 0
		self.Dict = {}

	def NewGame(self):
		self.data = self.data[1:] + self.data[:1]
		self.data = [player.ResetPlayer(self.PlayerNo) for player in self.data]

	def __getitem__(self, index: Union[int, str]):
		try:
			return super().__getitem__(index)
		except:
			return self.Dict[index]

	def __iter__(self):
		return iter(self.data)


class Player(object):
	"""Class object for representing a single player in the game."""
	__slots__ = '_name', 'playerindex', 'Hand', 'Bid', 'ActionComplete'

	AllPlayers = Gameplayers()

	def __init__(self, playerindex: int):
		self._name = playerindex
		self.playerindex = playerindex
		self.AllPlayers.append(self)
		self.Hand = Hand(self)
		self.Bid = -1
		self.ActionComplete = False

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, n: str):
		self._name = n
		self.AllPlayers.Dict[n] = self

	def ReceiveCards(self, cards, TrumpSuit):
		"""
		@type cards: list[src.Cards.ServerCard.ServerCard]
		@type TrumpSuit: src.Cards.Suit.Suit
		"""

		# Must receive an argument in the form of a list
		self.Hand.NewHand(cards, TrumpSuit)
		self.Hand.Iteration += 1
		return self

	def PlayCard(self, card, TrumpSuit):
		"""
		@type card: src.Cards.ServerCard.ServerCard
		@type TrumpSuit: src.Cards.Suit.Suit
		"""

		self.Hand.RemoveCard(card, TrumpSuit)
		self.Hand.Iteration += 1

	def ResetPlayer(self, PlayerNo: int):
		self.playerindex = (self.playerindex + 1) if self.playerindex < (PlayerNo - 1) else 0
		return self

	def __repr__(self):
		return self.name if isinstance(self.name, str) else f'Player with index {self.playerindex}, as yet unnamed'

	def __eq__(self, other):
		return self.name == other.name and self.Hand.Iteration == other.Hand.Iteration
