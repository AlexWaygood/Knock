from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar, Final

import src.static_constants as gc

from src.display.fireworks.firework_vars import FireworkVars
from src import DictLike

if TYPE_CHECKING:
	from src.special_knock_types import OptionalColours

	# noinspection PyTypeChecker
	C = TypeVar('C', bound='colour_scheme')


BLACK: Final       = (0, 0, 0)
MAROON: Final      = (128, 0, 0)
SILVER: Final      = (128, 128, 128)
LIGHT_GREY: Final  = (204, 204, 204)
BLACK_FADE: Final  = (0, 0, 0, FireworkVars.FadeRate)
ORANGE: Final      = (255, 136, 0)

# Opacities are given as single-item tuples to ensure consistency
OPAQUE_OPACITY: Final      = (255,)
TRANSLUCENT_OPACITY: Final = (0,)


THEMES = (
	gc.Theme(
		'Classic theme (dark red board)',
		SILVER,
		SILVER,
		MAROON,
		BLACK,
		BLACK
	),

	gc.Theme(
		'High contrast theme (orange board)',
		LIGHT_GREY,
		LIGHT_GREY,
		ORANGE,
		BLACK,
		BLACK
	)
)


# noinspection PyAttributeOutsideInit
class ColourScheme(DictLike):
	__slots__ = (
		gc.MENU_SCREEN_FILL_COLOUR, gc.SCOREBOARD_FILL_COLOUR, gc.GAMEPLAY_FILL_COLOUR, gc.TEXT_DEFAULT_FILL_COLOUR
	)

	OnlyColourScheme: OptionalColours   = None
	OpaqueOpacity: Final                = OPAQUE_OPACITY
	TranslucentOpacity: Final           = TRANSLUCENT_OPACITY

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	def __new__(cls: type[C], theme_key: str) -> C:
		cls.OnlyColourScheme = super(ColourScheme, cls).__new__(cls)
		return cls.OnlyColourScheme

	def __init__(self, theme_key: str) -> None:
		chosen_theme = next(theme for theme in THEMES if theme.description == theme_key)

		for slot in self.__slots__:
			self[slot] = getattr(chosen_theme, slot)

	def __repr__(self) -> str:
		return '\n'.join((
			'Colour scheme for the game.',
			'\n-'.join(f'{slot}: {self[slot]}.' for slot in self.__slots__),
			'\n\n'
		))
