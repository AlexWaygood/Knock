from __future__ import annotations

from typing import Literal, NamedTuple, Annotated, Any, overload
from fractions import Fraction
from functools import lru_cache
from contextlib import suppress
from math import ceil
from src import Dimensions
from src.static_constants import DIMENSIONS_OF_CARD_IMAGES_ON_HARD_DRIVE, DimensionConstants, BiddingChoices


def __dir__() -> list[str]:
	return [
		'player_number', 'bidding_system', 'card_resize_ratio_at_game_start',
		'frozen_state', 'screen_size', 'game_dimensions'
	]


### Game configuration - these are set ONCE, externally, at the start of the game. ###
### Their value is unknown at the very start of the programme. ###
player_number: Literal[2, 3, 4, 5, 6]
bidding_system: BiddingChoices
card_resize_ratio_at_game_start: Fraction


### Dynamic variables that are computed INTERNALLY the first time they are asked for.
frozen_state: bool
screen_size: Dimensions
game_dimensions: GameDimensions


@overload
def __getattr__(name: Literal['frozen_state']) -> bool: ...


@overload
def __getattr__(name: Literal['screen_size']) -> Dimensions: ...


@overload
def __getattr__(name: Literal['game_dimensions']) -> GameDimensions: ...


def __getattr__(name: str) -> Any:
	if name == 'frozen_state':
		return determine_if_we_are_compiled()
	if name == 'screen_size':
		return get_screen_size()
	if name == 'game_dimensions':
		return get_game_dimensions(
			window_dimensions=get_screen_size(),
			current_card_dimensions=DIMENSIONS_OF_CARD_IMAGES_ON_HARD_DRIVE
		)


def determine_if_we_are_compiled() -> bool:
	"""Determine if we have been compiled by pyinstaller or not."""

	global frozen_state

	import sys
	from os import chdir
	from warnings import filterwarnings

	if getattr(sys, 'frozen', False):
		# noinspection PyUnresolvedReferences,PyProtectedMember
		chdir(sys._MEIPASS)
		filterwarnings("ignore")
		frozen_state = True
	else:
		frozen_state = False

	return frozen_state


def get_screen_size() -> Dimensions:
	"""Try to calculate the size of the client's screen, fall back to default values if that doesn't work."""

	global screen_size

	with suppress(NameError):
		return screen_size

	try:
		from screeninfo import get_monitors
	except ModuleNotFoundError:
		# Default to some dimensions that we know the game works okay with.
		screen_size = Dimensions(
			width=DimensionConstants.DEFAULT_MAX_WIDTH,
			height=DimensionConstants.DEFAULT_MAX_HEIGHT
		)
	else:
		monitor = get_monitors()[0]
		screen_size = Dimensions(monitor.width, monitor.height)

	return screen_size


### Globals shared across multiple modules -- these are set at the start of the game, and ALSO altered at runtime. ###


class GameDimensions(NamedTuple):
	"""A tuple describing the dimensions of the game."""

	window_margin: Annotated[int, "The space between the left edge of the screen and the left edge of the game surface"]
	card_width: Annotated[int, "The width we want cards to be on the game surface"]
	card_height: Annotated[int, "The height we want cards to be on the game surface"]
	card_image_resize_ratio: Annotated[Fraction, "The ratio by which we need to resize the card images by"]


@lru_cache
def get_game_dimensions(
		*,
		window_dimensions: Dimensions,
		current_card_dimensions: Dimensions = DIMENSIONS_OF_CARD_IMAGES_ON_HARD_DRIVE
) -> GameDimensions:
	"""Calculate the window margin, card height, card width, and ratio by which the card images need to be resized.
	This function is used both at the beginning of the game and midway through the game.
	"""

	global game_dimensions

	# Calculate the required size of the card images,
	# based on various ratios of surfaces that will appear on the screen.

	# Lots of "magic numbers" here,
	# based purely on the principle of "keep the proportions that look good on my laptop".

	(game_width, game_height), (current_card_width, current_card_height) = window_dimensions, current_card_dimensions

	# The window margin is the space between the left edge of the screen and the left edge of the game surface.
	window_margin = int(game_width * Fraction(15, 683))

	# The height we want cards to be on the game surface.
	new_card_height = ceil(min(((game_height // Fraction(768, 150)) - window_margin), (game_height // 5.5)))

	# The width we want cards to be on the game surface.
	new_card_width = ceil(new_card_height * Fraction(current_card_width, current_card_height))

	# The ratio by which we need to resize the card images by.
	card_image_resize_ratio = Fraction(current_card_height, new_card_height)

	game_dimensions = GameDimensions(
		window_margin=window_margin,
		card_width=new_card_width,
		card_height=new_card_height,
		card_image_resize_ratio=card_image_resize_ratio
	)

	return game_dimensions


# Classes shared across multiple modules
client = None
game = None

display_manager = None
typewriter = None
input_context = None
Errors = None
UserInput = None
Mouse = None
Scrollwheel = None

GameSurf = None
HandSurf = None
TrumpCardSurf = None
BoardSurf = None
