from dataclasses import dataclass
from src.Display.AbstractSurfaces.TextRendering import TextBlitsMixin
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator


@dataclass
class InputContext(TextBlitsMixin, SurfaceCoordinator):
	# Repr filled in automatically because it's a dataclass!

	TrickClickNeeded: bool = False
	ClickToStart: bool = False
	TypingNeeded: bool = False
	GameUpdatesNeeded: bool = False
	Message: str = ''
	font: str = ''
	GameReset: bool = False
	FireworksDisplay: bool = False

	def InputNeeded(self):
		return self.TypingNeeded or self.ClickToStart or self.TrickClickNeeded

	def ClicksNeeded(self):
		return self.ClickToStart or self.TrickClickNeeded

	def Update(self, ForceUpdate=False):
		if not self.Message:
			return None

		center = self.BoardCentre if self.game.StartPlay else self.GameSurf.attrs.centre
		self.GameSurf.attrs.surf.blit(self.GetTextHelper(self.Message, self.Fonts[self.font], (0, 0, 0), center=center))

	def __call__(self, **kwargs):
		# noinspection PyArgumentList
		self.__init__(**kwargs)
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__init__()
		return self
