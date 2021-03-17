from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple, TYPE_CHECKING

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect

if TYPE_CHECKING:
	from src.special_knock_types import Position


class Dimensions(NamedTuple):
	rect: Rect
	centre: Position
	dimensions: Position
	topleft: Position


# noinspection PyAttributeOutsideInit
class BaseKnockSurface:
	__slots__ = 'Width', 'Height', 'x', 'y', 'colour', 'attrs', 'surf', 'surfandpos'

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def Dimensions(
			self,
			x: int,
			y: int,
			width: int,
			height: int
	):

		return Dimensions(Rect(x, y, width, height), ((width / 2), (height / 2)), (width, height), (x, y))

	def SurfAndPos(self):
		self.attrs = self.Dimensions(self.x, self.y, self.Width, self.Height)

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def GetSurfHelper(self, dimensions, rect):
		surf = Surface(dimensions)
		return surf, (surf, rect)

	def GetSurf(self):
		self.surf, self.surfandpos = self.GetSurfHelper(self.attrs.dimensions, self.attrs.rect)
		self.fill()

	def fill(self):
		self.surf.fill(self.colour)
