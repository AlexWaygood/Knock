from PIL import Image
from fractions import Fraction
from os import path, get_terminal_size

from rich.text import Text
from rich.panel import Panel
from rich import print as rprint


def ConvertImage(name: str,
                 NewWidth: int):

	im = Image.open(path.join('Images', 'Suits', f'{name}.png'))
	ratio = Fraction(im.size[1], im.size[0]) * Fraction(55, 100)
	im = im.resize((NewWidth, int(NewWidth * ratio)))
	Ascii = ''.join((' ' if p else '@') for p in im.getdata())
	return [Ascii[i: i + NewWidth] for i in range(0, len(Ascii), NewWidth)]


# noinspection PyUnboundLocalVariable
def ASCIISuits(TextLength: int):
	try:
		terminal = get_terminal_size()
		width, height = terminal.columns, terminal.lines
	except OSError:
		width = 140
		height = 40

	Divisor = 5
	ClubsLength = 1000

	while ClubsLength > (height - TextLength):
		ImageWidth = width // Divisor

		Clubs, Diamonds, Hearts, Spades = [
			ConvertImage(string, ImageWidth) for string in ('Club', 'Diamond', 'Heart', 'Spade')
		]

		ClubsLength = len(Clubs)
		Divisor += 1

	buffer = ''.join(' ' for _ in range(((width - (ImageWidth * 4)) // 5)))

	for c, d, h, s in zip(Clubs, Diamonds, Hearts, Spades):
		yield ''.join((buffer, c, buffer, d, buffer, h, buffer, s, buffer))


t = ''.join((
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


text = Text(t, justify='center', style='bold white on red')
VerticalPadding = 3
TextLength = len(t.splitlines()) + (VerticalPadding * 2) + 6


def PrintIntroMessage(text: Text = text,
                      TextLength: int = TextLength,
                      VerticalPadding: int = VerticalPadding):

	for line in ASCIISuits(TextLength):
		print(line)

	rprint(Panel(text, padding=(VerticalPadding, 2), style="black"))
