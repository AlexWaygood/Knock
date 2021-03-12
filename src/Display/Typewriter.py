from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, List
from itertools import accumulate

from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator
from src.Display.AbstractSurfaces.TextRendering import GetCursor

if TYPE_CHECKING:
	from src.Display.AbstractSurfaces.TextRendering import FontAndLinesize
	from queue import Queue
	from pygame import Surface

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect
from pygame.time import delay


@dataclass
class Typewriter(SurfaceCoordinator):
	__slots__ = 'RenderedSteps', 'Index', 'Rect', 'Q', 'font'

	RenderedSteps: List[Optional[Surface]]
	Index: int
	Q: Queue
	Rect: Optional[Rect]
	font: Optional[FontAndLinesize]

	def __post_init__(self):
		self.AllSurfaces.append(self)
		self.font = self.Fonts['TypewriterFont']

	def Initialise(self):
		self.font = self.Fonts['TypewriterFont']

	def Type(self, text, WaitAfterwards=1200):
		"""
		@type text: str
		@type WaitAfterwards: int
		"""

		self.Q.put(text)

		while not self.Q.empty():
			delay(100)

		for _ in text:
			self.Index += 1
			delay(30)

		if WaitAfterwards:
			delay(WaitAfterwards)

		self.Index = -1

	def Update(self, ForceUpdate=False):
		if not self.Q.empty():
			self.Rect = Rect((0, 0), self.font.size((text := self.Q.get())))
			self.RenderedSteps = [self.font.render(step, False, (0, 0, 0)) for step in accumulate(text)]

		if self.Index == -1:
			return None

		with self.game:
			PlayStarted = self.game.StartPlay

		TypewrittenText = self.RenderedSteps[self.Index]
		self.Rect.center = self.BoardCentre if PlayStarted else self.GameSurf.attrs.centre
		SubRect = TypewrittenText.get_rect()
		SubRect.topleft = self.Rect.topleft
		self.GameSurf.attrs.surf.blits(GetCursor([(TypewrittenText, SubRect)], self.font))
