from __future__ import annotations

from typing import TYPE_CHECKING, List
from fractions import Fraction
from functools import lru_cache
from dataclasses import dataclass

from src.global_constants import ERROR_TITLE_FONT, ERROR_MESSAGES_FONT
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.surface_coordinator import SurfaceCoordinator

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import get_ticks as GetTicks

if TYPE_CHECKING:
	from collections import deque
	from src.special_knock_types import Blittable, T


MESSAGE_LIFESPAN = 5000
MAX_MESSAGE_NO = 5


# Magic numbers based on the principle of "what looks good on my laptop."
@lru_cache
def ErrorPosHelper(
		GameX: int,
		GameY: int
):
	return int(GameX * Fraction(550, 683)), int(GameY * Fraction(125, 192))


@dataclass(eq=False)
class Errors(TextBlitsMixin, SurfaceCoordinator):
	# Repr automatically defined as it's a dataclass!

	__slots__ = 'Messages', 'ThisPass', 'StartTime', 'Pos', 'Title', 'TitleFont', 'MessageFont'

	Messages: deque[Blittable]
	ThisPass: List[str]
	StartTime: int
	Title: Blittable

	def __post_init__(self) -> None:
		self.AllSurfaces.append(self)
		self.Initialise()

	# noinspection PyAttributeOutsideInit
	def Initialise(self: T) -> T:
		self.Pos = ErrorPosHelper(self.GameSurf.Width, self.GameSurf.Height)
		self.TitleFont = self.Fonts[ERROR_TITLE_FONT]
		self.MessageFont = self.Fonts[ERROR_MESSAGES_FONT]
		return self

	def Update(self, ForceUpdate: bool = False):
		self.ErrorMessages()

		if self.Messages and GetTicks() > self.StartTime + MESSAGE_LIFESPAN:
			self.Messages.clear()

		while len(self.Messages) > MAX_MESSAGE_NO:
			self.Messages.popleft()

		self.GameSurf.surf.blits(self.Messages)

	def Add(self, message) -> None:
		self.ThisPass.append(message)

	def ErrorMessages(self) -> None:
		if not self.ThisPass:
			return None

		self.StartTime = GetTicks()
		Name = name if isinstance((name := self.player.name), str) else 'player'

		if not self.Messages:
			if not self.Title:
				self.Title = self.GetText(f'Messages to {Name}:', self.TitleFont, center=self.Pos)

			self.Messages.append(self.Title)
			y = self.Pos[1] + self.MessageFont.linesize

		else:
			y = self.Messages[-1][1].y + self.MessageFont.linesize

		x = self.Pos[0]

		for Error in self.ThisPass:
			self.Messages.append(self.GetText(Error, self.MessageFont, center=(x, y)))
			y += self.MessageFont.linesize

	# Must define hash even though it's in the parent class, because it's a dataclass
	def __hash__(self) -> int:
		return id(self)
