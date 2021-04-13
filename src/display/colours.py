from __future__ import annotations
from typing import NamedTuple, TYPE_CHECKING
from src.display.fireworks.firework_vars import FireworkVars
from src.misc import DictLike

if TYPE_CHECKING:
	from src.special_knock_types import Colour, OptionalColours


BLACK       = (0, 0, 0)
MAROON      = (128, 0, 0)
SILVER      = (128, 128, 128)
LIGHT_GREY  = (204, 204, 204)
BLACK_FADE  = (0, 0, 0, FireworkVars.FadeRate)
ORANGE      = (255, 136, 0)

# Opacities are given as single-item tuples to ensure consistency
OPAQUE_OPACITY      = (255,)
TRANSLUCENT_OPACITY = (0,)


class Theme(NamedTuple):
	Description:    str
	MenuScreen:     Colour
	Scoreboard:     Colour
	GamePlay:       Colour
	TextDefault:    Colour


THEMES = (
	Theme(
		'Classic theme (dark red board)',
		SILVER,
		SILVER,
		MAROON,
		BLACK
	),

	Theme(
		'High contrast theme (orange board)',
		LIGHT_GREY,
		LIGHT_GREY,
		ORANGE,
		BLACK
	)
)


# noinspection PyAttributeOutsideInit
class ColourScheme(DictLike):
	__slots__ = 'MenuScreen', 'Scoreboard', 'GamePlay', 'TextDefault'

	OnlyColourScheme: OptionalColours   = None
	OpaqueOpacity                       = OPAQUE_OPACITY
	TranslucentOpacity                  = TRANSLUCENT_OPACITY

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	def __new__(cls, ThemeKey: str):
		cls.OnlyColourScheme = super(ColourScheme, cls).__new__(cls)
		return cls.OnlyColourScheme

	def __init__(self, ThemeKey: str):
		ChosenTheme = next(theme for theme in THEMES if theme.Description == ThemeKey)

		for slot in self.__slots__:
			self[slot] = getattr(ChosenTheme, slot)

	def __repr__(self):
		return '\n'.join((
			'Colour scheme for the game.',
			'\n-'.join(f'{slot}: {self[slot]}.' for slot in self.__slots__),
			'\n\n'
		))
