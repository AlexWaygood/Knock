from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar
from abc import abstractmethod
from src.config import game
from src.display.abstract_surfaces.base_knock_surface import BaseKnockSurface
from src.display.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList

	# noinspection PyTypeChecker
	K = TypeVar('K', bound='KnockSurface')


class KnockSurface(BaseKnockSurface, SurfaceCoordinator):
	__slots__ = 'iteration', '_on_screen'

	def __init__(self, /) -> None:
		self.iteration = 0
		self.initialise()
		self._on_screen = False
		self.all_surfaces.append(self)

	@property
	def on_screen(self, /) -> bool:
		return self._on_screen

	def activate(self, /) -> None:
		self._on_screen = True

	def deactivate(self, /) -> None:
		self._on_screen = False

	# This method is used from __init__ and from new_window_size
	def initialise(self: K, /) -> K:
		self.surf_dimensions()
		self.get_surf_and_pos()
		return self

	def update(self, /, *, force_update: bool = False) -> None:
		if self._on_screen:
			with game:
				server_iteration = game.triggers.Server.Surfaces[repr(self)]

			if server_iteration > self.iteration or force_update:
				self.iteration = server_iteration
				self.fill()
				self.surf.blits(self.get_surf_blits(), False)

			self.game_surf.surf.blit(*self.surfandpos)

	@abstractmethod
	def surf_dimensions(self, *args, **kwargs) -> None: ...

	@abstractmethod
	def get_surf_blits(self, /) -> BlitsList: ...
