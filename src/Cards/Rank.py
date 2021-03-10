from typing import Union
from src.DataStructures import OnlyAFixedNumber


class Rank(OnlyAFixedNumber):
	__slots__ = 'Rank', 'Value', 'VerboseRank'

	AllRanks = (2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A')

	RankMapper = {
		'J': 'Jack',
		'Q': 'Queen',
		'K': 'King',
		'A': 'Ace'
	}

	def __init__(self, rank):
		"""
		@type rank: Union[int, str]
		"""

		self.Rank = rank
		self.VerboseRank = self.RankMapper[rank] if isinstance(rank, str) else rank
		self.Value = self.AllRanks.index(rank) + 2

	def __str__(self):
		return f'{self.VerboseRank}'

	def __repr__(self):
		return f'{self.Rank}'

	def __lt__(self, other):
		return self.Value < other.Value

	def __gt__(self, other):
		return self.Value > other.Value

	def __eq__(self, other):
		return self.Value == other.Value
