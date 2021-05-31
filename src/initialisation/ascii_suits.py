from __future__ import annotations

from PIL import Image
from fractions import Fraction
from os import path, get_terminal_size
from typing import List, Iterator

from rich.text import Text
from rich.panel import Panel
from rich import print as rprint


DEFAULT_WIDTH = 140
DEFAULT_HEIGHT = 40
CLUBS_LENGTH_START_VALUE = 1000
DIVISOR_START_VALUE = 5
IMAGE_RESIZE_RATIO = Fraction(55, 100)
ASCII_ART_FILL_CHARACTER = '@'
IMAGE_NAMES = ('Club', 'Diamond', 'Heart', 'Spade')
TEXT_JUSTIFY = 'center'
TEXT_STYLE = 'bold white on red'
VERTICAL_PADDING = 3

TEXT_TO_PRINT = ''.join((
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


def GetPath(name: str) -> str:
	return path.join('Images', 'Suits', f'{name}.png')


def ConvertImage(
		name: str,
		NewWidth: int
) -> List[str]:

	im = Image.open(GetPath(name))
	ratio = Fraction(im.size[1], im.size[0]) * IMAGE_RESIZE_RATIO
	im = im.resize((NewWidth, int(NewWidth * ratio)))
	Ascii = ''.join((' ' if p else ASCII_ART_FILL_CHARACTER) for p in im.getdata())
	return [Ascii[i: i + NewWidth] for i in range(0, len(Ascii), NewWidth)]


# noinspection PyUnboundLocalVariable
def ASCIISuits(TextLength: int) -> Iterator[str]:
	try:
		terminal = get_terminal_size()
		width, height = terminal.columns, terminal.lines
	except OSError:
		width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT

	Divisor = DIVISOR_START_VALUE
	ClubsLength = CLUBS_LENGTH_START_VALUE

	while ClubsLength > (height - TextLength):
		ImageWidth = width // Divisor

		Clubs, Diamonds, Hearts, Spades = [
			ConvertImage(string, ImageWidth) for string in IMAGE_NAMES
		]

		ClubsLength = len(Clubs)
		Divisor += 1

	buffer = ''.join(' ' for _ in range(((width - (ImageWidth * 4)) // 5)))

	for c, d, h, s in zip(Clubs, Diamonds, Hearts, Spades):
		yield ''.join((buffer, c, buffer, d, buffer, h, buffer, s, buffer))


def PrintIntroMessage() -> None:
	# noinspection PyTypeChecker
	text = Text(TEXT_TO_PRINT, justify=TEXT_JUSTIFY, style=TEXT_STYLE)
	TextLength = len(TEXT_TO_PRINT.splitlines()) + (VERTICAL_PADDING * 2) + 6

	for line in ASCIISuits(TextLength):
		print(line)

	rprint(Panel(text, padding=(VERTICAL_PADDING, 2), style="black"))
