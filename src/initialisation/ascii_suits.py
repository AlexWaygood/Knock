"""Module for printing ASCII art to the terminal.
This creates a pretty "welcome" message when the client starts the game.
"""

from __future__ import annotations

from PIL import Image
from fractions import Fraction
from os import path, get_terminal_size
from typing import Iterator, Final, Literal, TYPE_CHECKING

from rich.text import Text
from rich.panel import Panel
from rich import print as rprint

if TYPE_CHECKING:
	SuitNameLiteral = Literal['Club', 'Diamond', 'Heart', 'Spade']
	SuitNameLiteralTuple = tuple[SuitNameLiteral, SuitNameLiteral, SuitNameLiteral, SuitNameLiteral]


CLUB: SuitNameLiteral = 'Club'
DIAMOND: SuitNameLiteral = 'Diamond'
HEART: SuitNameLiteral = 'Heart'
SPADE: SuitNameLiteral = 'Spade'

DEFAULT_WIDTH: Final = 140
DEFAULT_HEIGHT: Final = 40
CLUBS_LENGTH_START_VALUE: Final = 1000
DIVISOR_START_VALUE: Final = 5
IMAGE_RESIZE_RATIO: Final = Fraction(55, 100)
ASCII_ART_FILL_CHARACTER: Final = '@'
IMAGE_NAMES: Final[SuitNameLiteralTuple] = (CLUB, DIAMOND, HEART, SPADE)
TEXT_JUSTIFY: Final = 'center'
TEXT_STYLE: Final = 'bold white on red'
VERTICAL_PADDING: Final = 3

TEXT_TO_PRINT: Final = ''.join((
	'\n\n\n\n',
	'Welcome to Knock, a multiplayer card game developed by Alex Waygood!',
	'\n\n\n',
	'This game is written in Python, using the pygame library.',
	'\n\n\n',
	'Knock is a variant of contract whist, also known as diminishing whist or "Oh Hell". ',
	'To take a look at the rules of the game, see this website here:',
	'\n\n',
	'https://www.pagat.com/exact/ohhell.html',
	'\n\n\n\n'
))


def get_path(suit_name: SuitNameLiteral) -> str:
	"""Return the file path of an image of a specified suit."""
	return path.join('Images', 'Suits', f'{suit_name}.png')


def convert_image(suit_name: SuitNameLiteral, new_width: int) -> list[str]:
	"""Return a list of strings comprising ASCII art corresponding to a card suit."""

	im = Image.open(get_path(suit_name))
	ratio = Fraction(im.size[1], im.size[0]) * IMAGE_RESIZE_RATIO
	im = im.resize((new_width, int(new_width * ratio)))
	ascii_image = ''.join((' ' if p else ASCII_ART_FILL_CHARACTER) for p in im.getdata())
	return [ascii_image[i:(i + new_width)] for i in range(0, len(ascii_image), new_width)]


# noinspection PyUnboundLocalVariable
def ascii_suits(text_len: int) -> Iterator[str]:
	"""Yield successive lines of ASCII art such that the cards_grouped_by_suits_dict appear side by side, evenly spaced, in the terminal."""

	try:
		terminal = get_terminal_size()
	except OSError:
		width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
	else:
		width, height = terminal.columns, terminal.lines

	divisor = DIVISOR_START_VALUE
	clubs_length = CLUBS_LENGTH_START_VALUE

	while clubs_length > (height - text_len):
		image_width = width // divisor

		clubs, diamonds, hearts, spades = [
			convert_image(string, image_width) for string in IMAGE_NAMES
		]

		clubs_length = len(clubs)
		divisor += 1

	buffer = ''.join(' ' for _ in range(((width - (image_width * 4)) // 5)))

	for c, d, h, s in zip(clubs, diamonds, hearts, spades):
		yield ''.join((buffer, c, buffer, d, buffer, h, buffer, s, buffer))


def print_intro_message() -> None:
	"""Print an intro message to the terminal when the client opens the programme."""

	# noinspection PyTypeChecker
	text = Text(TEXT_TO_PRINT, justify=TEXT_JUSTIFY, style=TEXT_STYLE)
	text_length = len(TEXT_TO_PRINT.splitlines()) + (VERTICAL_PADDING * 2) + 6

	for line in ascii_suits(text_length):
		print(line)

	rprint(Panel(text, padding=(VERTICAL_PADDING, 2), style="black"))
