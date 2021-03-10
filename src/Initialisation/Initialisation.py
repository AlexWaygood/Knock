from os import get_terminal_size
from ipaddress import ip_address
from socket import gethostbyname
from pyinputplus import inputCustom, inputMenu

from rich.text import Text
from rich.panel import Panel
from rich import print as rprint

from src.Network.AbstractPasswordChecker import PasswordInput
from src.Initialisation.ASCIISuits import Club, Diamond, Heart, Spade


def IPValidation(InputText: str):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = gethostbyname(InputText)
		ip_address(address)

	return InputText


text = Text(

	''.join((
		'\n\n\n\n\n',
		'Welcome to Knock, a multiplayer card game developed by Alex Waygood!',
		'\n\n\n',
		'This game is written in Python, using the pygame library.',
		'\n\n\n',
		'Knock is a variant of contract whist, also known as diminishing whist or "Oh Hell". ',
		'To take a look at the rules of the game, see this website here:',
		'\n\n',
		'https://www.pagat.com/exact/ohhell.html',
		'\n\n\n\n\n'
	)),

	justify='center',
	style='bold white on red'
)


def PrintIntroMessage(text=text):
	try:
		width = get_terminal_size().columns
	except OSError:
		width = 140

	Buffer = (width - 130) // 3

	for l1, l2, l3, l4 in zip(Club, Diamond, Heart, Spade):
		print(
			''.join((
				''.join(' ' for _ in range(5)),
				l1,
				''.join(' ' for _ in range(Buffer)),
				l2,
				''.join(' ' for _ in range(Buffer)),
				l3,
				''.join(' ' for _ in range(Buffer)),
				l4
			))
		)

	rprint(Panel(text, padding=(3, 2), style="black"))

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
	ThemeDict = {'Classic theme (dark red board)': 'Classic', 'High contrast theme (orange board)': 'High Contrast'}

	Theme = inputMenu(
		choices=ThemeChoices,
		prompt='Please select the colour theme you would like to play with:\n\n',
		numbered=True
	)

	return IP, Port, password, ThemeDict[Theme]
