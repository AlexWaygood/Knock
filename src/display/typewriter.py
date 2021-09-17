from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING, Final
from itertools import accumulate

from src.config import game
from src.static_constants import TYPEWRITER_FONT
from src.display import SurfaceCoordinator, get_cursor

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame import Rect
from pygame.time import delay

if TYPE_CHECKING:
	from src.display import FontAndLinesize
	from queue import Queue
	from pygame import Surface


TYPEWRITER_DELAY: Final = 30
TEXT_COLOUR: Final = (0, 0, 0)


@dataclass(eq=False, unsafe_hash=True)
class Typewriter(SurfaceCoordinator):
	__slots__ = 'rendered_steps', 'index', 'rect', 'q', 'font'

	rendered_steps: list[Surface]
	index: int
	q: Queue
	rect: Optional[rect]
	font: Optional[FontAndLinesize]

	def __post_init__(self) -> None:
		self.all_surfaces.append(self)
		self.font = self.fonts[TYPEWRITER_FONT]

	def initialise(self) -> Typewriter:
		self.font = self.fonts[TYPEWRITER_FONT]
		return self

	def type(self, text: str, /, *, wait_afterwards: int) -> None:
		self.q.put(text)

		while not self.q.empty():
			delay(100)

		for _ in text:
			self.index += 1
			delay(TYPEWRITER_DELAY)

		if wait_afterwards:
			delay(wait_afterwards)

		self.index = -1

	# Need to keep the unused keyword-arg in as it might be passed force_update=True
	def update(self, /, *, force_update: bool = False) -> None:
		if not self.q.empty():
			self.rect = Rect((0, 0), self.font.size((text := self.q.get())))
			self.rendered_steps = [self.font.render(step, False, TEXT_COLOUR) for step in accumulate(text)]

		if self.index == -1:
			return None

		with game:
			play_started = game.play_started

		typewritten_text = self.rendered_steps[self.index]
		self.rect.center = self.board_centre if play_started else self.game_surf.attrs.centre
		sub_rect = typewritten_text.get_rect()
		sub_rect.topleft = self.rect.topleft
		self.game_surf.surf.blits(get_cursor([(typewritten_text, sub_rect)], self.font))
