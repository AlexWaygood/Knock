from __future__ import annotations

from typing import TYPE_CHECKING, List
from fractions import Fraction
from functools import lru_cache
from dataclasses import dataclass

from src.display.abstract_surfaces.text_rendering import TextBlitsMixin
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import get_ticks as GetTicks

if TYPE_CHECKING:
	from collections import deque
	from src.special_knock_types import Blittable


@lru_cache
def ErrorPosHelper(GameX: int,
                   GameY: int):

	return int(GameX * Fraction(550, 683)), int(GameY * Fraction(125, 192))


@dataclass(eq=False, unsafe_hash=True)
class Errors(TextBlitsMixin, SurfaceCoordinator):
	# Repr & hash automatically defined as it's a dataclass!

	__slots__ = 'Messages', 'ThisPass', 'StartTime', 'Pos', 'Title', 'TitleFont', 'MessageFont'

	Messages: deque[Blittable]
	ThisPass: List[str]
	StartTime: int
	Title: Blittable

	def __post_init__(self):
		self.AllSurfaces.append(self)
		self.Initialise()

	# noinspection PyAttributeOutsideInit
	def Initialise(self):
		self.Pos = ErrorPosHelper(self.GameSurf.Width, self.GameSurf.Height)
		self.TitleFont = self.Fonts['ErrorTitleFont']
		self.MessageFont = self.Fonts['ErrorMessagesFont']

	def Update(self, ForceUpdate: bool = False):
		self.ErrorMessages()

		if self.Messages and GetTicks() > self.StartTime + 5000:
			self.Messages.clear()

		while len(self.Messages) > 5:
			self.Messages.popleft()

		self.GameSurf.surf.blits(self.Messages)

	def ErrorMessages(self):
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
