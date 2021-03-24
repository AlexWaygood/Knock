from __future__ import annotations

from typing import Sequence, TYPE_CHECKING
from src.display.abstract_surfaces.knock_surface import KnockSurface
from functools import lru_cache
from dataclasses import dataclass

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect

if TYPE_CHECKING:
	from src.special_knock_types import Position, RectList, CoverRectList
	from src.cards.client_card import ClientCard as Card


@dataclass(eq=False)
class CoverRect:
	__slots__ = 'surf', 'rect', 'surfandpos'

	surf: Surface
	rect: Rect

	def __post_init__(self):
		self.surfandpos = (self.surf, self.rect)

	def __hash__(self):
		return id(self)


# noinspection PyAttributeOutsideInit
class KnockSurfaceWithCards(KnockSurface):
	__slots__ = 'RectList', 'CardList', 'CoverRects', 'CardFadeManager', 'CardUpdateQueue', 'colour'

	def __init__(self):
		self.colour = self.ColourScheme.GamePlay
		self.RectList: RectList = []
		self.CoverRects: CoverRectList = []
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
			cv.surf.set_alpha(self.CardFadeManager.GetOpacity())

	def fill(self):
		self.surf.fill(self.colour)

		for cv in self.CoverRects:
			cv.surf.fill(self.colour)

		if (FadeOpacity := self.CardFadeManager.FadeInProgress()) is not False:
			for cv in self.CoverRects:
				cv.surf.set_alpha(FadeOpacity)

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
