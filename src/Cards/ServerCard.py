from src.Cards.Rank import Rank
from src.Cards.Suit import Suit
from src.DataStructures import OnlyAFixedNumber

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from typing import Union


class ServerCard(OnlyAFixedNumber):
	"""Class representing a playing card from a standard deck (excluding jokers)"""
	__slots__ = 'Rank', 'Suit', 'PlayedBy', 'ID'

	AllCards = []

	def __init__(self, rank, suit):
		"""
		@type rank: Union[int, str]
		@type suit: str
		"""

		self.Rank = Rank(rank)
		self.Suit = Suit(suit)
		self.ID = (rank, suit)
		self.PlayedBy = ''
		self.AllCards.append(self)

	def AddToHand(self, playername: str):
		self.PlayedBy = playername
		return self

	def __str__(self):
		return f'{self.Rank} of {self.Suit}'

	def __repr__(self):
		return f'{self.Rank!r}{self.Suit!r}'
