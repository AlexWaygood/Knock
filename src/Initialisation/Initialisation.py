from PIL import Image
from fractions import Fraction
from os import path, get_terminal_size
from ipaddress import ip_address
from socket import gethostbyname
from pyinputplus import inputCustom, inputMenu

from rich.text import Text
from rich.panel import Panel
from rich import print as rprint

from src.Network.AbstractPasswordChecker import PasswordInput


def ConvertImage(name, NewWidth):
	"""
	@type name: str
	@type NewWidth: int
	"""

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


def IPValidation(InputText: str):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = gethostbyname(InputText)
		ip_address(address)

	return InputText


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


def PrintIntroMessage(text=text, TextLength=TextLength, VerticalPadding=VerticalPadding):
	"""
	@type text: Text
	@type TextLength: int
	@type VerticalPadding: int
	"""

	for line in ASCIISuits(TextLength):
		print(line)

	rprint(Panel(text, padding=(VerticalPadding, 2), style="black"))

	# IP = 'alexknockparty.mywire.org'
	IP = '127.0.0.1'
	print('Connecting to local host.')
	Port = 5555
	# IP = inputCustom(IPValidation, 'Please enter the IP address or hostname of the server you want to connect to: ')
	# Port = inputInt('Please enter which port you wish to connect to: ', min=5000, max=65535)

	password = inputCustom(
		PasswordInput,
		'Please enter the password to connect to this game, if one has been set (press Enter if none has been set): ',
		blank=True
	)

	ThemeChoices = ['Classic theme (dark red board)', 'High contrast theme (orange board)']
	ThemeDict = {'Classic theme (dark red board)': 'Classic', 'High contrast theme (orange board)': 'Contrast'}

	Theme = inputMenu(
		choices=ThemeChoices,
		prompt='Please select the colour theme you would like to play with:\n\n',
		numbered=True
	)

	return IP, Port, password, ThemeDict[Theme]
