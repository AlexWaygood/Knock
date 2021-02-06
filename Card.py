from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect


class Card(object):
	"""Class representing a playing card from a standard deck (excluding jokers"""

	ValueMap = {11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace',
	            'D': 'Diamonds', 'C': 'Clubs', 'H': 'Hearts', 'S': 'Spades'}

	__slots__ = 'ActualValue', 'ActualSuit', 'WrittenValue', 'WrittenSuit', 'PlayedBy', 'ID', 'rect', 'colliderect', \
	            'image', 'surfandpos', 'CardSize'

	def __init__(self, ActualValue: int, ActualSuit: str):
		self.ActualValue = ActualValue
		self.ActualSuit = ActualSuit
		self.WrittenValue = self.ActualValue if (2 <= self.ActualValue <= 10) else self.ValueMap[self.ActualValue]
		self.WrittenSuit = self.ValueMap[self.ActualSuit]
		self.PlayedBy = ''
		self.ID = f'{self.ActualValue if self.ActualValue <= 10 else self.WrittenValue[0]}{self.ActualSuit}'
		self.CardSize = (79, 121)
		self.rect = Rect(0, 0, *self.CardSize)
		self.colliderect = Rect(0, 0, *self.CardSize)
		self.image = None
		self.surfandpos = None

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
		self.image = CardImages[self.ID]
		self.surfandpos = (self.image, self.rect)
		return self

	def GetWinValue(self, playedsuit, trumpsuit):
		if self.ActualSuit == playedsuit:
			return self.ActualValue
		return self.ActualValue + 13 if self.ActualSuit == trumpsuit else 0

	def __repr__(self):
		return f'{self.WrittenValue} of {self.WrittenSuit}'
