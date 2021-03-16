from __future__ import annotations

from functools import lru_cache, singledispatch
from fractions import Fraction
from time import time
from typing import overload, Union, TYPE_CHECKING

from src.data_structures import DictLike
from src.display.faders import ColourFader

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList, Position, Colour

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface
from pygame.font import SysFont


class FontAndLinesize:
	"""Class for holding data about various fonts that will be used frequently in the game"""
	__slots__ = 'font', 'linesize', 'Cursor'

	def __init__(self, font: SysFont):
		self.font = font
		self.linesize = font.get_linesize()
		self.Cursor = Surface((3, self.linesize))
		self.Cursor.fill((0, 0, 0))

	def __repr__(self):
		return f'FontAndLinesize object, style={Fonts.DefaultFont}, linesize={self.linesize}'

	def render(self, *args):
		return self.font.render(*args)

	def size(self, text: str):
		return self.font.size(text)


@overload
def GetCursor(TextAndPos: Union[Position, BlitsList], font: FontAndLinesize) -> BlitsList:
	pass


@singledispatch
def GetCursor(TextAndPos: tuple, font: FontAndLinesize):
	return [(font.Cursor, TextAndPos)] if time() % 1 > 0.5 else []


@GetCursor.register
def _(TextAndPos: list, font: FontAndLinesize):
	if time() % 1 > 0.5:
		TextAndPos.append((font.Cursor, TextAndPos[0][1].topright))
	return TextAndPos


@lru_cache
def FontMachine(GameX: int,
                GameY: int):

	x = 10
	NormalFont = SysFont(Fonts.DefaultFont, x, bold=True)
	UnderLineFont = SysFont(Fonts.DefaultFont, x, bold=True)

	while x < 19:
		x += 1
		font = SysFont(Fonts.DefaultFont, x, bold=True)
		font2 = SysFont(Fonts.DefaultFont, x, bold=True)
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
			SysFont(Fonts.DefaultFont, 20, bold=True),
			SysFont(Fonts.DefaultFont, 40, bold=True))
	]


class Fonts(DictLike):
	__slots__ = 'Normal', 'UnderLine', 'Massive', 'Title', 'TypewriterFont', 'UserInputFont', 'TrumpcardFont',\
	            'ErrorTitleFont', 'ErrorMessagesFont', 'StandardBoardFont', 'UnderlinedBoardFont', \
	            'NormalScoreboardFont', 'UnderlinedScoreboardFont'

	DefaultFont = 'Times New Roman'

	def __init__(self,
	             GameX: int,
	             GameY: int):

		Normal, UnderLine, Title, Massive = FontMachine(GameX, GameY)

		self.Normal = Normal
		self.UnderLine = UnderLine
		self.Title = Title
		self.Massive = Massive

		self.TypewriterFont = self.Normal
		self.UserInputFont = self.Normal
		self.TrumpcardFont = self.Normal

		self.ErrorTitleFont = self.Title
		self.ErrorMessagesFont = self.Normal

		self.StandardBoardFont = self.Normal
		self.UnderlinedBoardFont = self.UnderLine

		self.NormalScoreboardFont = self.Normal
		self.UnderlinedScoreboardFont = self.UnderLine

	def __repr__(self):
		return ''.join((
			f'Fonts-theme object: \n--',
			'\n--'.join(f"{f}: {self[f]}" for f in self.__slots__),
			'\n\n')
		)


# noinspection PyAttributeOutsideInit
class TextBlitsMixin:
	__slots__ = tuple()

	TextFade = ColourFader()

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

		if c := self.TextFadeManager.GetColour():
			self.TextColour = c
		return self.GetTextHelper(text, font, self.TextColour, **kwargs)

	def __hash__(self):
		return hash(repr(self))
