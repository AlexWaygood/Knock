"""Module for printing ASCII art to the terminal.
This creates a pretty "welcome" message when the client starts the game.
"""

from __future__ import annotations

from os import path, chdir, get_terminal_size as stdlib_get_terminal_size

if __name__ == '__main__':
	# For testing from the command line.
	import sys
	ROOT_DIRECTORY = r'C:\Users\Alex\Desktop\Code dump\Knock model\Final version - Local copy'
	sys.path.append(ROOT_DIRECTORY)
	chdir(ROOT_DIRECTORY)

from PIL import Image
from fractions import Fraction
from typing import Iterator, Final, NamedTuple, TypeVar
from src import Dimensions, StrEnum, cached_readonly_property

from rich.text import Text
from rich.panel import Panel
from rich import print as rich_print


DEFAULT_TERMINAL_DIMENSIONS: Final = Dimensions(140, 40)
DIVISOR_START_VALUE: Final = 5
IMAGE_RESIZE_RATIO: Final = Fraction(55, 100)
ASCII_ART_FILL_CHARACTER: Final = '@'
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


class ASCIISuits(StrEnum):
	"""Names of the four suits in a pack of cards"""

	CLUB = 'Club'
	DIAMOND = 'Diamond'
	HEART = 'Heart'
	SPADE = 'Spade'

	@cached_readonly_property
	def image(self, /) -> Image.Image:
		"""Get the image for this suit."""
		return Image.open(path.join('Images', 'Suits', f'{self}.png'))

	@cached_readonly_property
	def image_ratio(self, /) -> Fraction:
		"""[Description here.]"""
		width, height = self.image.size
		return Fraction(width, height) * IMAGE_RESIZE_RATIO

	def ascii_from_image(self, /, *, new_width: int) -> list[str]:
		"""Return a list of strings comprising ASCII art corresponding to this suit."""
		image, image_ratio = self.image, self.image_ratio
		image = image.resize((new_width, int(new_width * image_ratio)))
		ascii_image = ''.join((' ' if p else ASCII_ART_FILL_CHARACTER) for p in image.getdata())
		return [ascii_image[i:(i + new_width)] for i in range(0, len(ascii_image), new_width)]

	@classmethod
	def generate_all(cls, /, *, terminal_width: int, divisor: int, max_height: int) -> list[list[str]]:
		"""Return a list of lists, with each sublist representing ASCII art for a single suit."""
		all_suits = [suit.ascii_from_image(new_width=(terminal_width // divisor)) for suit in cls]

		while len(all_suits[0]) > max_height:
			all_suits = [suit.ascii_from_image(new_width=(terminal_width // divisor)) for suit in cls]
			divisor += 1

		return all_suits


def get_terminal_dimensions(default_dimensions=DEFAULT_TERMINAL_DIMENSIONS) -> Dimensions:
	"""Attempt to get the dimensions of the terminal, return a fallback if an error arises."""
	try:
		terminal = stdlib_get_terminal_size()
	except OSError:
		return default_dimensions
	else:
		return Dimensions(terminal.columns, terminal.lines)


# noinspection PyTypeChecker
P = TypeVar('P', bound='PrintableSuits')


class PrintableSuits(NamedTuple):
	"""All the info required for printing the ASCII suits"""

	ascii_clubs: list[str]
	ascii_diamonds: list[str]
	ascii_hearts: list[str]
	ascii_spades: list[str]
	buffer: str

	@classmethod
	def generate(cls: type[P], *, number_of_preceding_lines_of_text: int) -> P:
		"""Get the width at which the images need to be displayed on the screen."""
		terminal_width, terminal_height = get_terminal_dimensions()

		clubs, diamonds, hearts, spades = ASCIISuits.generate_all(
			terminal_width=terminal_width,
			divisor=DIVISOR_START_VALUE,
			max_height=(terminal_height - number_of_preceding_lines_of_text)
		)

		# noinspection PyArgumentList
		return cls(
			ascii_clubs=clubs,
			ascii_diamonds=diamonds,
			ascii_hearts=hearts,
			ascii_spades=spades,
			buffer=''.join(' ' for _ in range(((terminal_width - (len(clubs[0]) * 4)) // 5)))
		)

	def iter_lines(self, /) -> Iterator[str]:
		"""Yield successive lines of ASCII art such that suits appear side by side, evenly spaced, in the terminal."""

		*suits, buffer = self

		for suit_tuple in zip(*suits):
			yield f'{buffer}{buffer.join(suit_tuple)}{buffer}'


def print_intro_message() -> None:
	"""Print an intro message to the terminal when the client opens the programme."""

	# noinspection PyTypeChecker
	text = Text(TEXT_TO_PRINT, justify=TEXT_JUSTIFY, style=TEXT_STYLE)
	number_of_preceding_lines = len(TEXT_TO_PRINT.splitlines()) + (VERTICAL_PADDING * 2) + 6
	suits: PrintableSuits = PrintableSuits.generate(number_of_preceding_lines_of_text=number_of_preceding_lines)

	for line in suits.iter_lines():
		print(line)

	rich_print(Panel(text, padding=(VERTICAL_PADDING, 2), style="black"))


def test_intro_message() -> None:
	"""Test this module.

	To run this test:
		- Open up a terminal window.
		- cd C:\Users\Alex\Desktop\Code dump\Knock model\Final version - Local copy\src\initialisation
		- conda activate WebGame39
		- python ascii_suits.py
	"""

	from src.initialisation.maximise_window import maximise_window
	maximise_window()
	print_intro_message()


if __name__ == '__main__':
	test_intro_message()
