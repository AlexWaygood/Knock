from __future__ import annotations

from functools import lru_cache, singledispatch
from fractions import Fraction
from time import time
from typing import overload, TYPE_CHECKING, Final

from src.display.faders import ColourFader

import src.static_constants as gc

# noinspection PyUnresolvedReferences
from src import pre_pygame_import, DictLike, Dimensions
from pygame import Surface
from pygame.font import SysFont

if TYPE_CHECKING:
	from src.special_knock_types import Blittable, BlitsList, Colour, PositionOrBlitsList, OptionalColourFader


DEFAULT_TYPING_CURSOR_COLOUR: Final = (0, 0, 0)
DEFAULT_TYPING_CURSOR_WIDTH: Final = 3
TYPING_CURSOR_BLINKS_PER_SECOND: Final = 2
DEFAULT_FONT: Final = 'Times New Roman'
DEFAULT_BOLD: Final = True
TITLE_FONT_SIZE: Final = 20
MASSIVE_FONT_SIZE: Final = 40
# The size for the standard font is determined dynamically based on the user's screensize


class FontAndLinesize:
	"""Class for holding data about various fonts that will be used frequently in the game"""
	__slots__ = 'font', 'linesize', 'Cursor'

	def __init__(self, font: SysFont, /) -> None:
		self.font = font
		self.linesize = font.get_linesize()
		self.Cursor = Surface((DEFAULT_TYPING_CURSOR_WIDTH, self.linesize))
		self.Cursor.fill(DEFAULT_TYPING_CURSOR_COLOUR)

	def __repr__(self, /) -> str:
		return f'FontAndLinesize object, style={Fonts.DefaultFont}, linesize={self.linesize}'

	def render(self, *args) -> Surface:
		return self.font.render(*args)

	def size(self, text: str, /) -> Dimensions:
		return Dimensions(*self.font.size(text))

	def __hash__(self) -> int:
		return id(self)


def cursor_needed() -> bool:
	"""Return `True` if a cursor should be blitted to the screen, else `False`."""
	return (time() % 1) > (1 / TYPING_CURSOR_BLINKS_PER_SECOND)


@overload
def get_cursor(text_and_pos: PositionOrBlitsList, font: FontAndLinesize) -> BlitsList: ...


@singledispatch
def get_cursor(text_and_pos: tuple, font: FontAndLinesize):
	return [(font.Cursor, text_and_pos)] if cursor_needed() else []


@get_cursor.register
def _(text_and_pos: list, font: FontAndLinesize):
	if cursor_needed():
		text_and_pos.append((font.Cursor, text_and_pos[0][1].topright))
	return text_and_pos


@lru_cache
def font_machine(game_x: int, game_y: int) -> list[FontAndLinesize]:
	x = 10
	normal_font = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)
	underline_font = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)

	while x < 19:
		x += 1
		font = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)
		font2 = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)
		size = font.size('Trick not in progress')

		if size[0] > int(game_x * Fraction(70, 683)) or size[1] > int(game_y * Fraction(18, 768)):
			break

		normal_font = font
		underline_font = font2

	underline_font.set_underline(True)

	fonts = (
		normal_font,
		underline_font,
		SysFont(DEFAULT_FONT, TITLE_FONT_SIZE, bold=DEFAULT_BOLD),
		SysFont(DEFAULT_FONT, MASSIVE_FONT_SIZE, bold=DEFAULT_BOLD)
	)

	return [FontAndLinesize(font) for font in fonts]


class Fonts(DictLike):
	__slots__ = (
		gc.STANDARD_NORMAL_FONT, gc.STANDARD_UNDERLINE_FONT, gc.STANDARD_MASSIVE_FONT, gc.STANDARD_TITLE_FONT,
		gc.TYPEWRITER_FONT, gc.USER_INPUT_FONT, gc.TRUMP_CARD_FONT, gc.ERROR_TITLE_FONT, gc.ERROR_MESSAGES_FONT,
		gc.STANDARD_BOARD_FONT, gc.UNDERLINED_BOARD_FONT, gc.NORMAL_SCOREBOARD_FONT, gc.UNDERLINED_SCOREBOARD_FONT
	)

	DefaultFont = DEFAULT_FONT

	@classmethod
	def set_default_font(cls, /, font: str, *, bold_font: bool) -> None:
		cls.DefaultFont = font
		cls.DefaultBold = bold_font

	def __init__(self, game_x: int, game_y: int) -> None:
		normal, underline, title, massive = font_machine(game_x, game_y)

		self.Normal = normal
		self.UnderLine = underline
		self.Title = title
		self.Massive = massive

		self.TypewriterFont = self.Title
		self.UserInputFont = self.Normal
		self.TrumpcardFont = self.Normal

		self.ErrorTitleFont = self.Title
		self.ErrorMessagesFont = self.Normal

		self.StandardBoardFont = self.Normal
		self.UnderlinedBoardFont = self.UnderLine

		self.NormalScoreboardFont = self.Normal
		self.UnderlinedScoreboardFont = self.UnderLine

	def __repr__(self) -> str:
		return ''.join((
			f'Fonts-theme object: \n--',
			'; '.join(f"{f}: {self[f]}" for f in self.__slots__),
			'\n\n')
		)


# noinspection PyAttributeOutsideInit
class TextBlitsMixin:
	__slots__ = tuple()

	TextFade: OptionalColourFader = None

	@classmethod
	def add_text_fader(cls) -> None:
		cls.TextFade = ColourFader('TextDefault')

	@lru_cache
	def get_text_helper(
			self,
			text: str,
			font: FontAndLinesize,
			colour: Colour,
			**kwargs
	) -> Blittable:

		rendered = font.render(text, False, colour)
		return rendered, rendered.get_rect(**kwargs)

	# noinspection PyUnresolvedReferences
	# Can't add TextFadeManager to __slots__ as this would lead to a class-inheritance conflict
	def get_text(
			self,
			text: str,
			font: FontAndLinesize,
			**kwargs
	) -> Blittable:
		return self.get_text_helper(text, font, self.TextFade.get_colour(), **kwargs)

	# This method can't be inherited by dataclasses, which have to explicitly redefine __hash__()
	def __hash__(self) -> int:
		return id(self)
