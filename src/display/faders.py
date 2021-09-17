from __future__ import annotations

from typing import Sequence, TYPE_CHECKING, ClassVar
# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import delay, get_ticks
from src.display.colours import ColourScheme

if TYPE_CHECKING:
	from src.special_knock_types import Colour, OptionalColours, IntOrBool


class Fader:
	__slots__ = 'fade', 'start_time', 'end_time', 'fade_colour_1', 'fade_colour_2', 'colour', 'time_to_take', 'lock'

	colour_scheme: ClassVar[OptionalColours] = None

	def __init__(self, colour: str, *args, **kwargs) -> None:
		self.fade = False
		self.start_time = 0
		self.end_time = 0
		self.colour = self.colour_scheme[colour]
		self.fade_colour_1 = tuple()
		self.fade_colour_2 = tuple()
		self.time_to_take = 0

	def do_fade(self, /, *, colour1: Colour, colour2: Colour, time_to_take: int) -> None:
		self.fade = True
		self.start_time = get_ticks()
		self.fade_colour_1 = colour1
		self.fade_colour_2 = colour2
		self.time_to_take = time_to_take
		self.end_time = get_ticks() + time_to_take

	def get_colour_helper(self, elapsed_time: int, i: int) -> int:
		step = self.fade_colour_1[i] + (((self.fade_colour_2[i] - self.fade_colour_1[i]) / self.time_to_take) * elapsed_time)
		if step < 0:
			return 0
		if step > 255:
			return 255
		return int(step)

	def get_colour(self, /) -> Colour:
		if not self.fade:
			return self.colour

		if (time := get_ticks()) > self.end_time:
			self.fade = False
			self.colour = self.fade_colour_2
			return self.fade_colour_2

		elapsed = time - self.start_time
		return [self.get_colour_helper(elapsed, i) for i, _ in enumerate(self.fade_colour_1)]

	@classmethod
	def add_colour_scheme(cls, /) -> None:
		cls.colour_scheme: OptionalColours = ColourScheme.OnlyColourScheme


class ColourFader(Fader):
	__slots__ = tuple()

	def __call__(self, /, *, colour1: str, colour2: str, time_to_take: int) -> None:
		self.do_fade(
			colour1=self.colour_scheme[colour1],
			colour2=self.colour_scheme[colour2],
			time_to_take=time_to_take
		)

		delay(time_to_take)
		while self.fade:
			delay(50)


class OpacityFader(Fader):
	__slots__ = tuple()

	AllOpacityFaders = {}

	def __init__(self, /, *, start_opacity: str, name: str) -> None:
		super().__init__(start_opacity)
		self.AllOpacityFaders[name] = self

	def fade_in_progress(self, /) -> IntOrBool:
		return self.get_colour()[0] if self.fade else False

	@property
	def opacity(self, /) -> int:
		return self.get_colour()[0]

	@classmethod
	def card_fade(cls, /, surfaces: Sequence[str], *, time_to_take: int, fade_in: bool) -> None:
		opacity1, opacity2 = (255, 0) if fade_in else (0, 255)

		for s in surfaces:
			cls.AllOpacityFaders[s].do_fade((opacity1,), (opacity2,), time_to_take)

		delay(time_to_take)

		while any(cls.AllOpacityFaders[s].fade for s in surfaces):
			delay(50)
