from typing import Union
from collections import UserList
from src.Players.SortHand import SortHand
from src.Cards.ServerCard import Suit


class Hand(UserList):
	__slots__ = 'Iteration', 'player'

	def __init__(self, player):
		"""
		@type player: src.Players.AbstractPlayers.Player
		"""

		super().__init__()
		self.Iteration = 0
		self.player = player

	# noinspection PyAttributeOutsideInit
	def NewHand(self, cards, TrumpSuit):
		"""
		@type cards: list[src.Cards.ServerCard.ServerCard]
		@type TrumpSuit: Suit
		"""

		self.data = cards
		if cards:
			self.sort(TrumpSuit)
			self.data = [card.AddToHand(self.player.name) for card in self.data]

	def RemoveCard(self, card, TrumpSuit):
		"""
		@type card: src.Cards.ServerCard.ServerCard
		@type TrumpSuit: Suit
		"""

		SuitTuple = (self.data[0].Suit, self.data[-1].Suit)
		self.data.remove(card)
		self.sort(TrumpSuit, PlayedSuit=card.Suit, SuitTuple=SuitTuple)

	def sort(self, TrumpSuit, PlayedSuit=None, SuitTuple=(None, None)):
		"""
		@type TrumpSuit: Suit
		@type PlayedSuit: Suit
		@type SuitTuple: tuple[Suit]
		"""

		self.data = SortHand(self.data, TrumpSuit, PlayedSuit=PlayedSuit, SuitTuple=SuitTuple)

	def __getitem__(self, item: Union[int, str]):
		try:
			return super().__getitem__(item)
		except:
			return next(card for card in self.data if repr(card) == item)

	def __iter__(self):
		return iter(self.data)
