from __future__ import annotations

from typing import Sequence, TYPE_CHECKING, List, Optional
from src.display.abstract_surfaces.knock_surface import KnockSurface
from functools import lru_cache
from dataclasses import dataclass

if TYPE_CHECKING:
	from src.special_knock_types import Position
	from src.cards.client_card import ClientCard as Card

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect


@dataclass
class CoverRect:
	__slots__ = 'surf', 'rect', 'surfandpos'

	surf: Surface
	rect: Rect

	def __post_init__(self):
		self.surfandpos = (self.surf, self.rect)


# noinspection PyAttributeOutsideInit
class KnockSurfaceWithCards(KnockSurface):
	__slots__ = 'CoverRectOpacity', 'GameSurfWidth', 'GameSurfHeight', 'RectList', 'CardList', 'CoverRects', \
	            'CardFadeManager', 'CardUpdateQueue'

	def __init__(self):
		self.CoverRectOpacity = 255
		self.RectList: List[Optional[Rect]] = []
		self.CoverRects: List[Optional[CoverRect]] = []
		super().__init__()

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def RectListHelper(
			self,
			CardX: int,
			CardY: int,
			*CardPositions: Position
	):

		a = [Rect(p[0], p[1], CardX, CardY) for p in CardPositions]
		b = [CoverRect(Surface((CardX, CardY)), rect) for rect in a]
		return a, b

	def AddRectList(self, CardPositions: Sequence[Position]):
		self.RectList, self.CoverRects = self.RectListHelper(self.CardX, self.CardY, *CardPositions)

		for cv in self.CoverRects:
			cv.surf.set_alpha(self.CoverRectOpacity)

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

	def UpdateCardRects(self, ForceUpdate: bool = False):
		UpdateNeeded = False

		if not self.CardUpdateQueue.empty():
			UpdateNeeded = True
			self.CardUpdateQueue.get()

		if UpdateNeeded or ForceUpdate:
			for i, card in enumerate(self.CardList):
				self.UpdateCard(card, i)

	# Placeholder method, to be overriden higher up in the inheritance chain
	def UpdateCard(
			self,
			card: Card,
			index: int
	):
		pass
