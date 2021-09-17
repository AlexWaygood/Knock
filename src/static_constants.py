from __future__ import annotations

from string import digits, ascii_letters, punctuation
from typing import NamedTuple, TYPE_CHECKING, Final
from aenum import NamedConstant
from enum import Enum

import src

if TYPE_CHECKING:
	from src.special_knock_types import Colour


class DimensionConstants(src.DocumentedNumericConstants):
	"""Global constants relating to game dimensions"""

	MIN_GAME_WIDTH = 1186, "The minimum width the game is allowed to be when zooming out"
	MIN_GAME_HEIGHT = 588, "The minimum width the game is allowed to be when zooming out"
	DEFAULT_MAX_WIDTH = 1300, "The max width of the game (default value; replaced by the screen width if available)"
	DEFAULT_MAX_HEIGHT = 680, "The max width of the game (default value; replaced by the screen height if available)"
	MINIMUM_WINDOW_DIMENSION = 10, "The minimum dimension of the window when zooming out"


# board_surf fonts
class BoardSurfFonts(str, Enum):
	STANDARD_BOARD_FONT = 'standard_board_font'
	UNDERLINED_BOARD_FONT = 'underlined_board_font'


class ScoreboardSurfFonts(str, Enum):
	NORMAL_SCOREBOARD_FONT = 'normal_scoreboard_font'
	UNDERLINED_SCOREBOARD_FONT = 'underlined_scoreboard_font'


class ErrorHandlerFonts(str, Enum):
	ERROR_TITLE_FONT = 'error_title_font'
	ERROR_MESSAGES_FONT = 'error_messages_font'


class MiscFonts(str, Enum):
	TYPEWRITER_FONT = 'typewriter_font'
	TRUMP_CARD_FONT = 'trump_card_font'
	USER_INPUT_FONT = 'user_input_font'


class StandardFonts(str, Enum):
	STANDARD_NORMAL_FONT = 'normal'
	STANDARD_UNDERLINE_FONT = 'underline'
	STANDARD_MASSIVE_FONT = 'massive'
	STANDARD_TITLE_FONT = 'title'


class ScoreboardTextKeys(str, Enum):
	"""Scoreboard keys used in scoreboard_surf and players_client."""
	CURRENT_SCORES = 'scores'
	GAMES_WON = 'games_won'


class TextAlignment(str, Enum):
	"""Text-alignment globals"""
	TOP_LEFT_ALIGN = 'topleft'
	TOP_RIGHT_ALIGN = 'topright'


class CardFaderNames(str, Enum):
	"""Card-fade manager names"""
	HAND_CARD_FADE_KEY = 'hand'
	BOARD_CARD_FADE_KEY = 'board'
	TRUMP_CARD_FADE_KEY = 'trump'


class FillColours(str, Enum):
	"""Colour keys.
	Important that all these constants are the same as the variable player_names in the Theme class below.
	"""

	SCOREBOARD_FILL_COLOUR = 'scoreboard'
	MENU_SCREEN_FILL_COLOUR = 'menu_screen'
	GAMEPLAY_FILL_COLOUR = 'game_play'
	TEXT_DEFAULT_FILL_COLOUR = 'text_default'
	FIREWORKS_FILL_COLOUR = 'fireworks'


# Needs to be the same string as the class variable in colours.py
OPAQUE_OPACITY_KEY: Final = 'opaque_opacity'


class Theme(NamedTuple):
	description:    str
	menu_screen:    Colour
	scoreboard:     Colour
	game_play:      Colour
	text_default:   Colour
	fireworks:      Colour


class BiddingChoices(str, Enum):
	CLASSIC_BIDDING_SYSTEM = 'Classic'
	RANDOM_BIDDING_SYSTEM = 'Random'


class ContextConstants(str, Enum):
	MESSAGE = 'message'
	FONT = 'font'
	GAME_UPDATES_NEEDED = 'game_updates_needed'
	CLICK_TO_START = 'click_to_start'
	TRICK_CLICK_NEEDED = 'trick_click_needed'
	TYPING_NEEDED = 'typing_needed'
	GAME_RESET = 'game_reset'
	FIREWORKS_DISPLAY = 'fireworks_display'

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		pass


class StringConstants(NamedConstant):
	"""Constants for passwords and text input."""

	PRINTABLE_CHARACTERS = ''.join((digits, ascii_letters, punctuation))
	PRINTABLE_CHARACTERS_PLUS_SPACE = PRINTABLE_CHARACTERS + ' '


# The original size of the images used for the cards
DIMENSIONS_OF_CARD_IMAGES_ON_HARD_DRIVE: Final = src.Dimensions(691, 1056)

#
