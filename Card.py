from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect


class Card(object):
	"""Class representing a playing card from a standard deck (excluding jokers"""

	ActualValue: int
	ActualSuit: str

	__slots__ = 'ActualValue', 'ActualSuit', 'WrittenValue', 'WrittenSuit', 'PlayedBy', 'ID', 'rect', 'colliderect'

	def __init__(self, ActualValue: int, ActualSuit: str):
		self.ActualValue = ActualValue
		self.ActualSuit = ActualSuit

		ValueMap = {11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace',
		            'D': 'Diamonds', 'C': 'Clubs', 'H': 'Hearts', 'S': 'Spades'}

		self.WrittenValue = self.ActualValue if (2 <= self.ActualValue <= 10) else ValueMap[self.ActualValue]
		self.WrittenSuit = ValueMap[self.ActualSuit]
		self.PlayedBy = ''
		self.ID = f'{self.ActualValue if self.ActualValue <= 10 else self.WrittenValue[0]}{self.ActualSuit}'
		self.rect = Rect(0, 0, 79, 121)
		self.colliderect = Rect(0, 0, 79, 121)

	def AddToHand(self, playername):
		self.PlayedBy = playername
		return self

	def UpdateOnArrival(self, index, Surface, PlayerOrder, Surfaces):
		"""To be used on the client-side only"""
		index = PlayerOrder[index] if Surface == 'Board' else index
		self.rect = Surfaces[Surface].RectList[index]
		self.colliderect = self.rect.move(*Surfaces[Surface].pos)
		return self

	def GetWinValue(self, playedsuit, trumpsuit):
		if self.ActualSuit == playedsuit:
			return self.ActualValue
		return self.ActualValue + 13 if self.ActualSuit == trumpsuit else 0

	def Click(self, PlayedCards, PlayedByHand, MousePos):
		if not self.colliderect.collidepoint(*MousePos):
			return 'Not clicked'

		if PlayedCards:
			SuitLed = PlayedCards[0].ActualSuit
			Condition = any(UnplayedCard.ActualSuit == SuitLed for UnplayedCard in PlayedByHand)

			if self.ActualSuit != SuitLed and Condition:
				return 'You tried to play an illegal move! Maybe try again?'

		return None

	def __repr__(self):
		return f'{self.WrittenValue} of {self.WrittenSuit}'
