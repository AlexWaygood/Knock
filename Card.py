from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect


class Card(object):
	"""Class representing a playing card from a standard deck (excluding jokers"""

	ValueMap = {11: 'J', 12: 'Q', 13: 'K', 14: 'A'}

	VerboseDict = {'J': 'Jack', 'Q': 'Queen', 'A': 'Ace', 'K': 'King',
	               '♢': 'Diamonds', '♠': 'Spades', '♣': 'Clubs', '♡': 'Hearts'}

	__slots__ = 'ActualValue', 'Suit', 'WrittenValue', 'PlayedBy', 'rect', 'colliderect', 'image', 'surfandpos', \
	            'CardSize', 'VerboseString'

	def __init__(self, ActualValue: int, Suit: str):
		self.ActualValue = ActualValue
		self.Suit = Suit
		self.WrittenValue = self.ActualValue if self.ActualValue < 11 else self.ValueMap[self.ActualValue]
		self.PlayedBy = ''
		self.CardSize = (79, 121)
		self.rect = Rect(0, 0, *self.CardSize)
		self.colliderect = Rect(0, 0, *self.CardSize)
		self.image = None
		self.surfandpos = None
		VerboseValue = self.WrittenValue if isinstance(self.WrittenValue, int) else self.VerboseDict[self.WrittenValue]
		self.VerboseString = f'{VerboseValue} of {self.VerboseDict[self.Suit]}'

	def AddToHand(self, playername):
		self.PlayedBy = playername
		return self

	def UpdateOnArrival(self, index, Surface, PlayerOrder, Surfaces, CardImages):
		"""

		To be used on the client-side only.
		Can be used after the cards have arrived on the client side, if the user is resizing the board mid-game.

		"""

		index = PlayerOrder[index] if Surface == 'Board' else index
		self.rect = Surfaces[Surface].RectList[index]
		self.colliderect = self.rect.move(*Surfaces[Surface].pos).move(*Surfaces['Game'].topleft)
		self.image = CardImages[f'{self}']
		self.surfandpos = (self.image, self.rect)
		return self

	def GetWinValue(self, playedsuit, trumpsuit):
		if self.Suit == playedsuit:
			return self.ActualValue
		return self.ActualValue + 13 if self.Suit == trumpsuit else 0

	def __repr__(self):
		return f'{self.WrittenValue}{self.Suit}'
