from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import image
from itertools import product
from HelperFunctions import CardResizer
from typing import Union


CardSuits = ('♢', '♠', '♣', '♡')
AllRanks = (2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A')
AllCardValues = tuple(product(AllRanks, CardSuits))


class Suit(object):

	__slots__ = 'suit', 'VerboseSuit', 'IsBlack'

	SuitMapper = {
		'♢': 'Diamonds',
		'♠': 'Clubs',
		'♣': 'Clubs',
		'♡': 'Hearts'
	}

	AllSuits = []
	Blacks = ('♣', '♠')
	Reds = ('♡', '♢')

	def __new__(cls, suit):
		try:
			return next(s for s in cls.AllSuits if f'{s!r}' == suit)
		except:
			return super(Suit, cls).__new__(cls)

	def __init__(self, suit):
		self.suit = suit
		self.VerboseSuit = self.SuitMapper[self.suit]
		self.IsBlack = (suit in self.Blacks)
		self.AllSuits.append(self)

	def __repr__(self):
		return self.suit

	def __str__(self):
		return self.VerboseSuit

	def __eq__(self, other):
		assert isinstance(other, Suit), "Can't compare 'Suit' object with a different kind of object"
		return self.suit == other.suit

	def __getnewargs__(self):
		return self.suit,


class Rank(object):

	__slots__ = 'Rank', 'Value', 'VerboseRank'

	RankMapper = {
		'J': 'Jack',
		'Q': 'Queen',
		'K': 'King',
		'A': 'Ace'
	}

	AllInstantiatedRanks = []

	def __new__(cls, rank):
		try:
			return next(r for r in cls.AllInstantiatedRanks if f'{r!r}' == rank)
		except:
			return super(Rank, cls).__new__(cls)

	def __init__(self, rank, AllRanks=AllRanks):
		self.Rank = rank
		self.VerboseRank = self.RankMapper[rank] if isinstance(rank, str) else rank
		self.Value = AllRanks.index(rank) + 2
		self.AllInstantiatedRanks.append(self)

	def __str__(self):
		return f'{self.VerboseRank}'

	def __repr__(self):
		return f'{self.Rank}'

	def __lt__(self, other):
		assert isinstance(other, Rank), "Can't compare 'Rank' object with a different kind of object"
		return self.Value < other.Value

	def __gt__(self, other):
		assert isinstance(other, Rank), "Can't compare 'Rank' object with a different kind of object"
		return self.Value > other.Value

	def __eq__(self, other):
		assert isinstance(other, Rank), "Can't compare 'Rank' object with a different kind of object"
		return self.Value == other.Value

	def __getnewargs__(self):
		return self.Rank,


class Card(object):
	"""Class representing a playing card from a standard deck (excluding jokers"""

	__slots__ = 'Rank', 'Suit', 'PlayedBy', 'rect', 'colliderect', 'image', 'surfandpos', 'CardSize', 'ID'

	AllCards = []
	BaseCardImages = {}
	CardImages = {}

	def __new__(cls, rank, suit):
		try:
			return next(card for card in cls.AllCards if card.ID == (rank, suit))
		except:
			return super(Card, cls).__new__(cls)

	def __init__(self, rank: Union[str, int], suit: str):
		self.Rank = Rank(rank)
		self.Suit = Suit(suit)
		self.ID = (rank, suit)
		self.PlayedBy = ''
		self.AllCards.append(self)

	def AddToHand(self, playername):
		self.PlayedBy = playername
		return self

	# noinspection PyAttributeOutsideInit
	def ReceiveRect(self, rect, SurfPos, GameSurfPos):
		self.rect = rect
		self.colliderect = rect.move(*SurfPos).move(*GameSurfPos)
		self.surfandpos = (self.image, self.rect)

	def GetWinValue(self, playedsuit, trumpsuit):
		if self.Suit == playedsuit:
			return self.Rank.Value
		return self.Rank.Value + 13 if self.Suit == trumpsuit else 0

	@classmethod
	def AddCardImages(cls, CardImages):
		cls.BaseCardImages = {
			ID: image.fromstring(im.tobytes(), im.size, im.mode).convert()
			for ID, im in CardImages.items()
		}

		cls.CardImages = cls.BaseCardImages.copy()

	@classmethod
	def UpdateCardImages(cls, ResizeRatio):
		cls.CardImages = CardResizer(ResizeRatio, cls.BaseCardImages)

		for card in cls.AllCards:
			card.image = cls.CardImages[repr(card)]

	def __str__(self):
		return f'{self.Rank} of {self.Suit}'

	def __repr__(self):
		return f'{self.Rank!r}{self.Suit!r}'

	def __getnewargs__(self):
		return repr(self.Rank), repr(self.Suit)


AllCards = tuple([Card(rank, suit) for rank, suit in AllCardValues])
