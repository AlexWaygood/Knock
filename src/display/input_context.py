from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.special_knock_types import InputContextTypeVar, ExitArg1, ExitArg2, ExitArg3


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

	def __post_init__(self) -> None:
		self.AllSurfaces.append(self)

	def InputNeeded(self) -> bool:
		return self.TypingNeeded or self.ClickToStart or self.TrickClickNeeded

	def ClicksNeeded(self) -> bool:
		return self.ClickToStart or self.TrickClickNeeded

	# Might be passed ForceUpdate=True, so need to keep the **kwargs argument in.
	def Update(self, **kwargs) -> None:
		if not self.Message:
			return None

		center = self.BoardCentre if self.game.StartPlay else self.GameSurf.attrs.centre
		self.GameSurf.surf.blit(
			*self.GetTextHelper(self.Message, self.Fonts[self.font], (0, 0, 0), center=center)
		)

	def __call__(self: InputContextTypeVar, **kwargs) -> InputContextTypeVar:
		# noinspection PyArgumentList
		self.__init__(**kwargs)
		return self

	def __enter__(self: InputContextTypeVar) -> InputContextTypeVar:
		return self

	def __exit__(
			self: InputContextTypeVar,
			exc_type: ExitArg1,
			exc_val: ExitArg2,
			exc_tb: ExitArg3
	) -> InputContextTypeVar:

		self.__init__()
		return self
