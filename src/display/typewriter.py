from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from itertools import accumulate

from src.display.surface_coordinator import SurfaceCoordinator
from src.display.abstract_text_rendering import GetCursor

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect
from pygame.time import delay

if TYPE_CHECKING:
	from src.display.abstract_text_rendering import FontAndLinesize
	from src.special_knock_types import SurfaceList
	from queue import Queue


FONT = 'TypewriterFont'
TYPEWRITER_DELAY = 30
TEXT_COLOUR = (0, 0, 0)


@dataclass(eq=False, unsafe_hash=True)
class Typewriter(SurfaceCoordinator):
	__slots__ = 'RenderedSteps', 'Index', 'Rect', 'Q', 'font'

	RenderedSteps: SurfaceList
	Index: int
	Q: Queue
	Rect: Optional[Rect]
	font: Optional[FontAndLinesize]

	def __post_init__(self):
		self.AllSurfaces.append(self)
		self.font = self.Fonts[FONT]

	def Initialise(self):
		self.font = self.Fonts[FONT]
		return self

	def Type(self,
	         text: str,
	         WaitAfterwards: int):

		self.Q.put(text)

		while not self.Q.empty():
			delay(100)

		for _ in text:
			self.Index += 1
			delay(TYPEWRITER_DELAY)

		if WaitAfterwards:
			delay(WaitAfterwards)

		self.Index = -1

	# Need to keep **kwargs in as it might be passed ForceUpdate=True
	def Update(self, **kwargs):
		if not self.Q.empty():
			self.Rect = Rect((0, 0), self.font.size((text := self.Q.get())))
			self.RenderedSteps = [self.font.render(step, False, TEXT_COLOUR) for step in accumulate(text)]

		if self.Index == -1:
			return None

		with self.game:
			PlayStarted = self.game.StartPlay

		TypewrittenText = self.RenderedSteps[self.Index]
		self.Rect.center = self.BoardCentre if PlayStarted else self.GameSurf.attrs.centre
		SubRect = TypewrittenText.get_rect()
		SubRect.topleft = self.Rect.topleft
		self.GameSurf.surf.blits(GetCursor([(TypewrittenText, SubRect)], self.font))
