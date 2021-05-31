from __future__ import annotations

from string import digits, ascii_letters, punctuation
from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
	from src.special_knock_types import Colour

# BoardSurf fonts
STANDARD_BOARD_FONT = 'StandardBoardFont'
UNDERLINED_BOARD_FONT = 'UnderlinedBoardFont'

# ScoreboardSurf fonts
NORMAL_SCOREBOARD_FONT = 'NormalScoreboardFont'
UNDERLINED_SCOREBOARD_FONT = 'UnderlinedScoreboardFont'

# ErrorHandler Fonts
ERROR_TITLE_FONT = 'ErrorTitleFont'
ERROR_MESSAGES_FONT = 'ErrorMessagesFont'

# Other fonts
TYPEWRITER_FONT = 'TypewriterFont'
TRUMP_CARD_FONT = 'TrumpCardFont'
USER_INPUT_FONT = 'UserInputFont'

STANDARD_NORMAL_FONT = 'Normal'
STANDARD_UNDERLINE_FONT = 'Underline'
STANDARD_MASSIVE_FONT = 'Massive'
STANDARD_TITLE_FONT = 'Title'

# Scoreboard keys used in scoreboard_surf and players_client
SCOREBOARD_TEXT_KEY_1 = 'point'
SCOREBOARD_TEXT_KEY_2 = 'game'

# Text-alignment globals
TOP_LEFT_ALIGN = 'topleft'
TOP_RIGHT_ALIGN = 'topright'

# Card-fade manager names
HAND_CARD_FADE_KEY = 'Hand'
BOARD_CARD_FADE_KEY = 'Board'
TRUMP_CARD_FADE_KEY = 'Trump'

# Colour keys - important that all these constants are the same as the variable names in the Theme class below.
SCOREBOARD_FILL_COLOUR = 'Scoreboard'
MENU_SCREEN_FILL_COLOUR = 'MenuScreen'
GAMEPLAY_FILL_COLOUR = 'GamePlay'
TEXT_DEFAULT_FILL_COLOUR = 'TextDefault'
FIREWORKS_FILL_COLOUR = 'Fireworks'

# Needs to be the same string as the class variable in colours.py
OPAQUE_OPACITY_KEY = 'OpaqueOpacity'


class Theme(NamedTuple):
	Description:    str
	MenuScreen:     Colour
	Scoreboard:     Colour
	GamePlay:       Colour
	TextDefault:    Colour
	Fireworks:      Colour


CLASSIC_BIDDING_SYSTEM = 'Classic'
RANDOM_BIDDING_SYSTEM = 'Random'

# Constants for use with input_context.py
MESSAGE = 'Message'
FONT = 'font'
GAME_UPDATES_NEEDED = 'GameUpdatesNeeded'
CLICK_TO_START = 'ClickToStart'
TRICK_CLICK_NEEDED = 'TrickClickNeeded'
TYPING_NEEDED = 'TypingNeeded'
GAME_RESET = 'Gamereset'
FIREWORKS_DISPLAY = 'FireworksDisplay'

# Constants for passwords and text input.
PRINTABLE_CHARACTERS = ''.join((digits, ascii_letters, punctuation))
PRINTABLE_CHARACTERS_PLUS_SPACE = PRINTABLE_CHARACTERS + ' '

ORIGINAL_CARD_IMAGE_DIMENSIONS = (691, 1056)
