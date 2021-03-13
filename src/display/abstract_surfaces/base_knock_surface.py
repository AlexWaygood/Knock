from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple, TYPE_CHECKING

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect
from pygame import error as PGerror

if TYPE_CHECKING:
	from src.special_knock_types import Position, Blittable


class Dimensions(NamedTuple):
	surf: Surface
	rect: Rect
	centre: Position
	surfandpos: Blittable
	dimensions: Position
	topleft: Position


# noinspection PyAttributeOutsideInit
class BaseKnockSurface:
	__slots__ = 'Width', 'Height', 'x', 'y', 'colour', 'attrs'

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def SurfRectCentre(
			self,
			x: int,
			y: int,
			width: int,
			height: int
	):

		try:
			surf, rect, centre = Surface((width, height)), Rect(x, y, width, height), ((width / 2), (height / 2))
		except PGerror as e:
			print(width, height)
			raise e

		return Dimensions(surf, rect, centre, (surf, rect), (width, height), (x, y))

	def SurfAndPos(self):
		self.attrs = self.SurfRectCentre(self.x, self.y, self.Width, self.Height)
		self.fill()

	def fill(self):
		self.attrs.surf.fill(self.colour)