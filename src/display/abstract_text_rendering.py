from __future__ import annotations

from functools import lru_cache, singledispatch
from fractions import Fraction
from time import time
from typing import overload, TYPE_CHECKING

from src.misc import DictLike
from src.display.faders import ColourFader

from src.global_constants import (
	STANDARD_BOARD_FONT,
	UNDERLINED_BOARD_FONT,
	NORMAL_SCOREBOARD_FONT,
	UNDERLINED_SCOREBOARD_FONT,
	TRUMP_CARD_FONT,
	TYPEWRITER_FONT,
	USER_INPUT_FONT,
	ERROR_MESSAGES_FONT,
	ERROR_TITLE_FONT,
	STANDARD_MASSIVE_FONT,
	STANDARD_NORMAL_FONT,
	STANDARD_TITLE_FONT,
	STANDARD_UNDERLINE_FONT
)

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame import Surface
from pygame.font import SysFont

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList, Colour, PositionOrBlitsList, OptionalColourFader


DEFAULT_TYPING_CURSOR_COLOUR = (0, 0, 0)
DEFAULT_TYPING_CURSOR_WIDTH = 3
TYPING_CURSOR_BLINKS_PER_SECOND = 2
DEFAULT_FONT = 'Times New Roman'
DEFAULT_BOLD = True
TITLE_FONT_SIZE = 20
MASSIVE_FONT_SIZE = 40
# The size for the standard font is determined dynamically based on the user's screensize


class FontAndLinesize:
	"""Class for holding data about various fonts that will be used frequently in the game"""
	__slots__ = 'font', 'linesize', 'Cursor'

	def __init__(self, font: SysFont):
		self.font = font
		self.linesize = font.get_linesize()
		self.Cursor = Surface((DEFAULT_TYPING_CURSOR_WIDTH, self.linesize))
		self.Cursor.fill(DEFAULT_TYPING_CURSOR_COLOUR)

	def __repr__(self) -> str:
		return f'FontAndLinesize object, style={Fonts.DefaultFont}, linesize={self.linesize}'

	def render(self, *args) -> Surface:
		return self.font.render(*args)

	def size(self, text: str):
		return self.font.size(text)

	def __hash__(self) -> int:
		return id(self)


def CursorNeeded() -> bool:
	return (time() % 1) > (1 / TYPING_CURSOR_BLINKS_PER_SECOND)


@overload
def GetCursor(TextAndPos: PositionOrBlitsList, font: FontAndLinesize) -> BlitsList:
	pass


@singledispatch
def GetCursor(TextAndPos: tuple, font: FontAndLinesize) -> BlitsList:
	return [(font.Cursor, TextAndPos)] if CursorNeeded() else []


@GetCursor.register
def _(TextAndPos: list, font: FontAndLinesize) -> BlitsList:
	if CursorNeeded():
		TextAndPos.append((font.Cursor, TextAndPos[0][1].topright))
	return TextAndPos


@lru_cache
def FontMachine(GameX: int, GameY: int):
	x = 10
	NormalFont = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)
	UnderLineFont = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)

	while x < 19:
		x += 1
		font = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)
		font2 = SysFont(DEFAULT_FONT, x, bold=DEFAULT_BOLD)
		Size = font.size('Trick not in progress')

		if Size[0] > int(GameX * Fraction(70, 683)) or Size[1] > int(GameY * Fraction(18, 768)):
			break

		NormalFont = font
		UnderLineFont = font2

	UnderLineFont.set_underline(True)

	return [
		FontAndLinesize(font) for font in (
			NormalFont,
			UnderLineFont,
			SysFont(DEFAULT_FONT, TITLE_FONT_SIZE, bold=DEFAULT_BOLD),
			SysFont(DEFAULT_FONT, MASSIVE_FONT_SIZE, bold=DEFAULT_BOLD)
		)
	]


class Fonts(DictLike):
	__slots__ = STANDARD_NORMAL_FONT, STANDARD_UNDERLINE_FONT, STANDARD_MASSIVE_FONT, STANDARD_TITLE_FONT, \
	            TYPEWRITER_FONT, USER_INPUT_FONT, TRUMP_CARD_FONT, ERROR_TITLE_FONT, ERROR_MESSAGES_FONT, \
	            STANDARD_BOARD_FONT, UNDERLINED_BOARD_FONT,  NORMAL_SCOREBOARD_FONT, UNDERLINED_SCOREBOARD_FONT

	DefaultFont = DEFAULT_FONT

	@classmethod
	def SetDefaultFont(
			cls,
			font: str,
			BoldFont: bool
	):
		cls.DefaultFont = font
		cls.DefaultBold = BoldFont

	def __init__(
			self,
			GameX: int,
			GameY: int
	):

		Normal, UnderLine, Title, Massive = FontMachine(GameX, GameY)

		self.Normal = Normal
		self.UnderLine = UnderLine
		self.Title = Title
		self.Massive = Massive

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
	def AddTextFader(cls) -> None:
		cls.TextFade = ColourFader('TextDefault')

	@lru_cache
	def GetTextHelper(
			self,
			text: str,
			font: FontAndLinesize,
			colour: Colour,
			**kwargs
	):

		text = font.render(text, False, colour)
		return text, text.get_rect(**kwargs)

	# noinspection PyUnresolvedReferences
	# Can't add TextFadeManager to __slots__ as this would lead to a class-inheritance conflict
	def GetText(
			self,
			text: str,
			font: FontAndLinesize,
			**kwargs
	):
		return self.GetTextHelper(text, font, self.TextFade.GetColour(), **kwargs)

	# This method can't be inherited by dataclasses, which have to explicitly redefine __hash__()
	def __hash__(self) -> int:
		return id(self)
