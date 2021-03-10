from typing import Sequence
from src.Display.AbstractSurfaces.KnockSurface import KnockSurface
from os import environ
from functools import lru_cache
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect


class CoverRect(object):
	__slots__ = 'surf', 'rect', 'surfandpos'

	def __init__(self, rect, CardDimensions, Opacity):
		"""
		@type rect: Rect
		@type CardDimensions: tuple
		@type Opacity: int
		"""

		self.surf = Surface(CardDimensions)
		self.rect = rect
		self.surf.set_alpha(Opacity)
		self.surfandpos = (self.surf, self.rect)


# noinspection PyAttributeOutsideInit
class KnockSurfaceWithCards(KnockSurface):
	__slots__ = 'CoverRectOpacity', 'GameSurfWidth', 'GameSurfHeight', 'RectList', 'CardList', 'CoverRects', \
	            'CardFadeManager', 'CardUpdateQueue'

	def __init__(self):
		super().__init__()
		self.CoverRectOpacity = 255

	@lru_cache
	def RectListHelper(self, CardPositions: Sequence):
		a = [Rect(p[0], p[1], self.CardX, self.CardY) for p in CardPositions]
		b = [CoverRect(rect, (self.CardX, self.CardY), self.CoverRectOpacity) for rect in self.RectList]
		return a, b

	def AddRectList(self, CardPositions: Sequence):
		self.RectList, self.CoverRects = self.RectListHelper(CardPositions)

	def fill(self):
		super().fill()

		for cv in self.CoverRects:
			cv.surf.fill(self.colour)

		if op := self.CardFadeManager.GetOpacity():
			self.CoverRectOpacity = op
			for cv in self.CoverRects:
				cv.surf.set_alpha(op)

	def GetSurfBlits(self):
		self.UpdateCardRects()
		L = [card.surfandpos for card in self.CardList]

		if self.CardFadeManager and self.CardList:
			L += [cv.surfandpos for cv in self.CoverRects[:len(self.CardList)]]

		return L

	def UpdateCardRects(self, ForceUpdate=False):
		UpdateNeeded = False

		if not self.CardUpdateQueue.empty():
			UpdateNeeded = True
			self.CardUpdateQueue.get()

		if UpdateNeeded or ForceUpdate:
			for i, card in enumerate(self.CardList):
				self.UpdateCard(card, i)

	# Placeholder method, to be overriden higher up in the inheritance chain
	def UpdateCard(self, card, index):
		"""
		@type card: src.Cards.ClientCard.ClientCard
		@type index: int
		"""
		pass
