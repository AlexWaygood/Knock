from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect


class Card(object):
	"""Class representing a playing card from a standard deck (excluding jokers"""

	ActualValue: int
	ActualSuit: str

	__slots__ = 'ActualValue', 'ActualSuit', 'value', 'suit', 'PlayedBy', 'winvalue', 'ID', 'rect', 'colliderect', \
	            'CurrentTrumpSuit', 'Suits'

	OriginalSuits = ['C', 'D', 'S', 'H']

	def __init__(self, ActualValue: int, ActualSuit: str):
		self.ActualValue = ActualValue
		self.ActualSuit = ActualSuit

		ValueMap = {11: 'Jack', 12: 'Queen', 13: 'King', 14: 'Ace',
		            'D': 'Diamonds', 'C': 'Clubs', 'H': 'Hearts', 'S': 'Spades'}

		self.value = self.ActualValue if (2 <= self.ActualValue <= 10) else ValueMap[self.ActualValue]
		self.suit = ValueMap[self.ActualSuit]
		self.PlayedBy = 'Undetermined'
		self.winvalue = 0
		self.ID = f'{self.ActualValue if self.ActualValue <= 10 else self.value[0]}{self.ActualSuit}'
		self.rect = Rect(0, 0, 79, 121)
		self.colliderect = Rect(0, 0, 79, 121)
		self.CurrentTrumpSuit = ''
		self.Suits = self.OriginalSuits.copy()

	def AddToHand(self, playerindex):
		self.PlayedBy = playerindex
		return self

	def UpdateOnArrival(self, index, Surface, PlayerOrder, Surfaces):
		"""To be used on the client-side only"""
		index = PlayerOrder[index] if Surface == 'Board' else index
		self.rect = Surfaces[Surface].RectList[index]
		self.colliderect = self.rect.move(*Surfaces[Surface].pos)
		return self

	def DetermineWinValue(self, playedsuit, trump):
		self.winvalue = self.ActualValue if self.ActualSuit == playedsuit else (
			self.ActualValue + 13 if self.ActualSuit == trump else 0)
		return self

	def GetWinValue(self):
		return self.winvalue

	def SetTrumpSuit(self, TrumpSuit):
		self.CurrentTrumpSuit = TrumpSuit
		TrumpIndex = Card.OriginalSuits.index(self.CurrentTrumpSuit)
		self.Suits = Card.OriginalSuits[(TrumpIndex + 1):] + Card.OriginalSuits[:(TrumpIndex + 1)]
		return self

	def SuitAndValue(self):

		"""Method for sorting the cards in a player's hand, in most eventualities"""

		return self.Suits.index(self.ActualSuit), self.ActualValue

	def SuitAndValueWithoutDiamonds(self):

		"""

		Method for sorting the cards in a player's hand, in the eventuality...
		 ...that the only suit the player lacks is Diamonds

		"""

		SuitDict = {
			'C': 3 if self.CurrentTrumpSuit == 'C' else 1,
			'H': 2,
			'S': 1 if self.CurrentTrumpSuit == 'C' else 3
		}

		return SuitDict[self.ActualSuit], self.ActualValue

	def SuitAndValueWithoutSpades(self):

		"""

		Method for sorting the cards in a player's hand, in the eventuality...
		...that the only suit the player lacks is Spades

		"""

		SuitDict = {
			'D': 3 if self.CurrentTrumpSuit == 'D' else 1,
			'C': 2,
			'H': 1 if self.CurrentTrumpSuit == 'D' else 3
		}

		return SuitDict[self.ActualSuit], self.ActualValue

	def SuitAndValueWithoutHearts(self):

		"""

		Method for sorting the cards in a player's hand, in the eventuality...
		...that the only suit the player lacks is Hearts

		"""

		SuitDict = {
			'S': 3 if self.CurrentTrumpSuit == 'S' else 1,
			'D': 2,
			'C': 1 if self.CurrentTrumpSuit == 'S' else 3
		}

		return SuitDict[self.ActualSuit], self.ActualValue

	def SuitAndValueWithoutClubs(self):

		"""

		Method for sorting the cards in a player's hand, in the eventuality...
		...that the only suit the player lacks is Clubs

		"""

		SuitDict = {
			'H': 3 if self.CurrentTrumpSuit == 'H' else 1,
			'S': 2,
			'D': 1 if self.CurrentTrumpSuit == 'H' else 3
		}

		return SuitDict[self.ActualSuit], self.ActualValue

	def Click(self, PlayedCards, PlayedByHand, MousePos):
		if not self.colliderect.collidepoint(*MousePos):
			return 'Not clicked'

		if PlayedCards:
			SuitLed = PlayedCards[0].ActualSuit

			Condition = any(
				UnplayedCard.ActualSuit == SuitLed
				for UnplayedCard in PlayedByHand
			)

			if self.ActualSuit != SuitLed and Condition:
				return 'You tried to play an illegal move! Maybe try again?'

		return None

	def __repr__(self):
		return f'{self.value} of {self.suit}'
