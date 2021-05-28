from __future__ import annotations
from typing import TYPE_CHECKING
from src.display.abstract_surfaces.base_knock_surface import BaseKnockSurface
from src.display.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.special_knock_types import KnockSurfaceTypeVar, BlitsList


class KnockSurface(BaseKnockSurface, SurfaceCoordinator):
	__slots__ = 'Iteration', 'OnScreen'

	def __init__(self) -> None:
		self.Iteration = 0
		self.Initialise()
		self.OnScreen = False
		self.AllSurfaces.append(self)

	def Activate(self) -> None:
		self.OnScreen = True

	def Deactivate(self) -> None:
		self.OnScreen = False

	# This method is used from __init__ and from NewWindowSize
	def Initialise(self: KnockSurfaceTypeVar) -> KnockSurfaceTypeVar:
		self.SurfDimensions()
		self.SurfAndPos()
		return self

	def Update(self, ForceUpdate: bool = False) -> None:
		if self.OnScreen:
			with self.game:
				ServerIteration = self.game.Triggers.Server.Surfaces[repr(self)]

			if ServerIteration > self.Iteration or ForceUpdate:
				self.Iteration = ServerIteration
				self.fill()
				self.surf.blits(self.GetSurfBlits(), False)

			self.GameSurf.surf.blit(*self.surfandpos)

	# Two placeholder methods, to be overriden higher up in the inheritance chain
	def SurfDimensions(self, *args, **kwargs) -> None:
		pass

	def GetSurfBlits(self) -> BlitsList:
		return []
