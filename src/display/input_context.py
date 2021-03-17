from dataclasses import dataclass
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator


@dataclass(eq=False, unsafe_hash=True)
class InputContext(TextBlitsMixin, SurfaceCoordinator):
	# Repr & hash filled in automatically because it's a dataclass!

	TrickClickNeeded: bool = False
	ClickToStart: bool = False
	TypingNeeded: bool = False
	GameUpdatesNeeded: bool = False
	Message: str = ''
	font: str = ''
	GameReset: bool = False
	FireworksDisplay: bool = False

	def __post_init__(self):
		self.AllSurfaces.append(self)

	def InputNeeded(self):
		return self.TypingNeeded or self.ClickToStart or self.TrickClickNeeded

	def ClicksNeeded(self):
		return self.ClickToStart or self.TrickClickNeeded

	# Might be passed ForceUpdate=True, so need to keep the **kwargs argument in.
	def Update(self, **kwargs):
		if not self.Message:
			return None

		center = self.BoardCentre if self.game.StartPlay else self.GameSurf.attrs.centre
		self.GameSurf.surf.blit(
			*self.GetTextHelper(self.Message, self.Fonts[self.font], (0, 0, 0), center=center)
		)

	def __call__(self, **kwargs):
		# noinspection PyArgumentList
		self.__init__(**kwargs)
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__init__()
		return self
