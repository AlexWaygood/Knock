from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple, TypeVar, Final
from fractions import Fraction
from functools import lru_cache
from dataclasses import dataclass

from src.static_constants import ERROR_TITLE_FONT, ERROR_MESSAGES_FONT
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.abstract_text_rendering import TextBlitsMixin

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import get_ticks

if TYPE_CHECKING:
	from collections import deque
	from src.special_knock_types import Blittable

	# noinspection PyTypeChecker
	E = TypeVar('E', bound='ErrorsPosition')


MESSAGE_LIFESPAN: Final = 5000
MAX_MESSAGE_NO: Final = 5


class ErrorsPosition(NamedTuple):
	x: int
	y: int

	@classmethod
	@lru_cache
	def from_game_dimensions(cls: type[E], /, *, game_x, game_y) -> E:
		# Magic numbers based on the principle of "what looks good on my laptop."
		# noinspection PyTypeChecker
		return cls(
			int(game_x * Fraction(550, 683)),
			int(game_y * Fraction(125, 192))
		)


@dataclass(eq=False)
class Errors(TextBlitsMixin, SurfaceCoordinator):
	# Repr automatically defined as it's a dataclass!

	__slots__ = 'messages', 'this_pass', 'start_time', 'pos', 'title', 'title_font', 'message_font'

	messages: deque[Blittable]
	this_pass: list[str]
	start_time: int
	title: Blittable

	def __post_init__(self) -> None:
		self.all_surfaces.append(self)
		self.initialise()

	# noinspection PyAttributeOutsideInit
	def initialise(self, /) -> Errors:
		self.pos = ErrorsPosition.from_game_dimensions(
			game_x=self.game_surf.width,
			game_y=self.game_surf.height
		)

		self.title_font = self.fonts[ERROR_TITLE_FONT]
		self.message_font = self.fonts[ERROR_MESSAGES_FONT]
		return self

	def update(self, /, *, force_update: bool = False) -> None:
		self.error_messages()

		if self.messages and get_ticks() > self.start_time + MESSAGE_LIFESPAN:
			self.messages.clear()

		while len(self.messages) > MAX_MESSAGE_NO:
			self.messages.popleft()

		self.game_surf.surf.blits(self.messages)

	def add(self, message, /) -> None:
		self.this_pass.append(message)

	def error_messages(self, /) -> None:
		if not self.this_pass:
			return None

		self.start_time = get_ticks()
		name = self.player.name
		name = name if isinstance(name, str) else 'player'

		if not self.messages:
			if not self.title:
				self.title = self.get_text(f'messages to {name}:', self.title_font, center=self.pos)

			self.messages.append(self.title)
			y = self.pos[1] + self.message_font.linesize

		else:
			y = self.messages[-1][1].y + self.message_font.linesize

		x = self.pos[0]

		for Error in self.this_pass:
			self.messages.append(self.get_text(Error, self.message_font, center=(x, y)))
			y += self.message_font.linesize

	# Must define hash even though it's in the parent class, because it's a dataclass
	def __hash__(self, /) -> int:
		return id(self)
