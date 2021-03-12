from functools import lru_cache
from collections import namedtuple
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect
from pygame import error as PGerror


Dimensions = namedtuple('Dimensions', ('surf', 'rect', 'centre', 'surfandpos', 'dimensions', 'topleft'))


# noinspection PyAttributeOutsideInit
class BaseKnockSurface:
	__slots__ = 'Width', 'Height', 'x', 'y', 'colour', 'attrs'

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def SurfRectCentre(self, x, y, width, height):
		"""
		@type x: int
		@type y: int
		@type width: int
		@type height: int
		"""
		try:
			surf, rect, centre = Surface((width, height)), Rect(x, y, width, height), ((width / 2), (height / 2))
		except PGerror as e:
			print(width, height)
			raise e

		surfandpos, dimensions, topleft = (surf, rect), (width, height), (x, y)
		return Dimensions(surf, rect, centre, surfandpos, dimensions, topleft)

	def SurfAndPos(self):
		self.attrs = self.SurfRectCentre(self.x, self.y, self.Width, self.Height)
		self.fill()

	def fill(self):
		self.attrs.surf.fill(self.colour)
