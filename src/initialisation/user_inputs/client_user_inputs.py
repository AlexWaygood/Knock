from __future__ import annotations
from typing import TYPE_CHECKING, Tuple
from socket import gethostbyname
from pprint import pprint
from pyinputplus import inputCustom, inputMenu, inputYesNo, RetryLimitException
from ipaddress import ip_address

from src.password_checker.password_abstract import PasswordInput
# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.font import init as pg_font_init, get_fonts

if TYPE_CHECKING:
	from src.special_knock_types import ThemeTuple


DEFAULT_THEME_INDEX = 0
FONT_ENTRY_MAX_ATTEMPTS = 3


def IPValidation(InputText: str) -> str:
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	# noinspection PyBroadException
	try:
		ip_address(InputText)
	except:
		address = gethostbyname(InputText)
		ip_address(address)

	return InputText


AllFonts = get_fonts()


# noinspection PyDefaultArgument,PyShadowingNames
def FontInput(FontName: str, AllFonts=AllFonts) -> str:
	"""Will raise an exception if the user enters an invalid font name"""
	assert FontName in AllFonts
	return FontName


SettingsChoices = ['Continue with default settings', 'Customise default font and colour theme for the game']


# noinspection PyShadowingNames,PyDefaultArgument
def UserInputs(
		themes: ThemeTuple,
		SettingsChoices=SettingsChoices,
		AllFonts=AllFonts
) -> Tuple[str, int, str, str, str, bool]:

	# IP = 'alexknockparty.mywire.org'
	IP = '127.0.0.1'
	print('Connecting to local host.')
	Port = 5555
	# IP = inputCustom(IPValidation, 'Please enter the IP address or hostname of the server you want to connect to: ')
	# Port = inputInt('Please enter which port you wish to connect to: ', min=5000, max=65535)

	password: str = inputCustom(
		PasswordInput,
		'Please enter the password to connect to this game, if one has been set (press Enter if none has been set): ',
		blank=True
	)

	SettingsChoice = inputMenu(
		choices=SettingsChoices,
		prompt='Select whether you would like to continue with default display settings, '
		       'or customise the font and colours'
		       '(press enter to continue with default settings):\n\n',
		numbered=True,
		blank=True
	)

	FontChoice, BoldFont = '', False

	if SettingsChoice == SettingsChoices[1]:
		FontChoice = input(
			'Please enter your preferred font for the game (press enter to default to Times New Roman):\n\n'
		)

		if FontChoice:
			pg_font_init()

			if FontChoice not in AllFonts:
				ViewAvailableFonts = inputYesNo(
					f'{FontChoice} is not a valid font. '
					f'Would you like to see a list of all available fonts on your machine? '
				)

				if ViewAvailableFonts == 'yes':
					pprint(get_fonts())

				try:
					FontChoice = inputCustom(
						FontInput,
						prompt='Please enter your preferred font for the game '
						       '(press enter to default to Times New Roman):\n\n',
						blank=True,
						limit=FONT_ENTRY_MAX_ATTEMPTS
					)

				except RetryLimitException:
					print('Defaulting to Times New Roman as you have failed to enter a valid font.')

		if FontChoice:
			BoldFont = inputYesNo(prompt='Would you like that font emboldened by default? ')

		# noinspection PyTypeChecker
		ChosenTheme = inputMenu(
			choices=[t.Description for t in themes],
			prompt='Please select the colour theme you would like to play with:\n\n',
			numbered=True
		)

	else:
		ChosenTheme = themes[DEFAULT_THEME_INDEX].Description

	return IP, Port, password, ChosenTheme, FontChoice, (BoldFont == 'yes')
