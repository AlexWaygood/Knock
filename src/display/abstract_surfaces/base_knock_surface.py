from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple, TYPE_CHECKING

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
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
	__slots__ = 'Width', 'Height', 'x', 'y', 'attrs', 'surf', 'surfandpos'

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

	def SurfAndPos(self) -> None:
		self.attrs = self.Dimensions(self.x, self.y, self.Width, self.Height)

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def GetSurfHelper(self, dimensions: Position):
		return Surface(dimensions)

	def GetSurf(self) -> None:
		self.surf = self.GetSurfHelper(self.attrs.dimensions)
		self.surfandpos = (self.surf, self.attrs.rect)
		self.fill()

	# Placeholder method, to be overriden higher up in the inheritance chain
	def fill(self) -> None:
		pass
