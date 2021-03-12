from functools import lru_cache
from fractions import Fraction
from time import time

from src.DataStructures import DictLike
from src.Display.Faders import ColourFader

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect
from pygame.font import SysFont


def GetCursor(text, font):
	"""
	@type text: list
	@type font: FontAndLinesize
	"""

	if time() % 1 > 0.5:
		text.append((font.Cursor, (position.topright if isinstance((position := text[0][1]), Rect) else position)))
	return text


class FontAndLinesize:
	"""Class for holding data about various fonts that will be used frequently in the game"""
	__slots__ = 'font', 'linesize', 'Cursor'

	def __init__(self, font: SysFont):
		self.font = font
		self.linesize = font.get_linesize()
		self.Cursor = Surface((3, self.linesize))
		self.Cursor.fill((0, 0, 0))

	def render(self, *args):
		return self.font.render(*args)

	def size(self, text):
		return self.font.size(text)


@lru_cache
def FontMachine(GameX, GameY):
	"""
	@type GameX: int
	@type GameY: int
	"""

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

	def __init__(self, GameX, GameY):
		"""
		@type GameX: int
		@type GameY: int
		"""

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


# noinspection PyAttributeOutsideInit
class TextBlitsMixin:
	__slots__ = tuple()

	TextFade = ColourFader()

	@lru_cache
	def GetTextHelper(self, text, font, colour, **kwargs):
		"""
		@type text: str
		@type font: FontAndLinesize
		@type colour: tuple
		"""

		text = font.render(text, False, colour)
		return text, text.get_rect(**kwargs)

	# noinspection PyUnresolvedReferences
	def GetText(self, text, font, **kwargs):
		"""
		@type text: str
		@type font: FontAndLinesize
		"""

		if c := self.TextFadeManager.GetColour():
			self.TextColour = c
		return self.GetTextHelper(text, font, self.TextColour, **kwargs)
