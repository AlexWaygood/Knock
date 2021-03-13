from src.data_structures import OnlyAFixedNumber
from typing import Any


class Suit(OnlyAFixedNumber):
	__slots__ = 'suit', 'VerboseSuit', 'IsBlack'

	SuitMapper = {
		'♢': 'Diamonds',
		'♠': 'Clubs',
		'♣': 'Clubs',
		'♡': 'Hearts'
	}

	CardSuits = ('♢', '♠', '♣', '♡')
	Blacks = ('♣', '♠')
	Reds = ('♡', '♢')

	def __init__(self, suit: str):
		self.suit = suit
		self.VerboseSuit = self.SuitMapper[self.suit]
		self.IsBlack = (suit in self.Blacks)

	def __repr__(self):
		return self.suit

	def __str__(self):
		return self.VerboseSuit

	def __eq__(self, other: Any):
		assert isinstance(other, Suit), "Can't compare 'Suit' object with a different kind of object"
		return self.suit == other.suit

	def __hash__(self):
		return hash(self.suit)
