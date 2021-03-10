from src.Display.AbstractSurfaces.BaseKnockSurface import BaseKnockSurface
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator


class KnockSurface(BaseKnockSurface, SurfaceCoordinator):
	__slots__ = 'Iteration', 'OnScreen'

	def __init__(self):
		self.colour = self.ColourScheme.GamePlay
		super().__init__()
		self.Iteration = 0
		self.Initialise()
		self.OnScreen = False
		self.AllSurfaces.append(self)

	def Activate(self):
		self.OnScreen = True

	def Deactivate(self):
		self.OnScreen = False

	# This method is used from __init__ and from NewWindowSize
	def Initialise(self):
		self.SurfDimensions()
		self.SurfAndPos()

	def Update(self, ForceUpdate=False):
		if not self.OnScreen:
			return None

		with self.game:
			ServerIteration = self.game.Triggers.Server.Surfaces[repr(self)]

		if ServerIteration > self.Iteration or ForceUpdate:
			self.Iteration = ServerIteration
			self.fill()
			self.attrs.surf.blits(self.GetSurfBlits(), False)

		self.GameSurf.attrs.surf.blit(self.attrs.surfandpos)

	# Two placeholder methods, to be overriden higher up in the inheritance chain
	def SurfDimensions(self, *args, **kwargs):
		pass

	def GetSurfBlits(self):
		return []
