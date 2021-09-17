from __future__ import annotations

from functools import lru_cache
from typing import NamedTuple, TYPE_CHECKING, TypeVar, Any
from abc import ABCMeta, abstractmethod

# noinspection PyUnresolvedReferences
from src import pre_pygame_import, Position, Dimensions
from pygame import Surface, Rect

if TYPE_CHECKING:
	# noinspection PyTypeChecker
	D = TypeVar('D', bound='Dimensions')


class KnockSurfaceDimensions(NamedTuple):
	rect: Rect
	centre: Position
	dimensions: Dimensions
	topleft: Position

	@classmethod
	@lru_cache
	def from_coordinates(cls: type[D], x: int, y: int, width: int, height: int) -> D:
		# noinspection PyArgumentList,PyTypeChecker
		return cls(
			rect=Rect(x, y, width, height),
			centre=Position((width / 2), (height / 2)),
			dimensions=Dimensions(width, height),
			topleft=Position(x, y)
		)


# noinspection PyAttributeOutsideInit
class BaseKnockSurface(metaclass=ABCMeta):
	__slots__ = 'dimensions', 'position', 'attrs', 'surf', 'surfandpos'

	def get_surf_and_pos(self) -> None:
		self.attrs = KnockSurfaceDimensions.from_coordinates(*self.position, *self.dimensions)

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def get_surf_helper(self, dimensions: Position) -> Surface:
		return Surface(dimensions)

	def get_surf(self) -> None:
		self.surf = self.get_surf_helper(self.attrs.dimensions)
		self.surfandpos = (self.surf, self.attrs.rect)
		self.fill()

	@abstractmethod
	def update(self, **kwargs: Any) -> Any: ...

	@abstractmethod
	def fill(self) -> None: ...
