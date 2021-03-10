from src.DataStructures import OnlyAFixedNumber


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

	def __eq__(self, other):
		assert isinstance(other, Suit), "Can't compare 'Suit' object with a different kind of object"
		return self.suit == other.suit
