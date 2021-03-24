from socket import gethostbyname
from pprint import pprint
from pyinputplus import inputCustom, inputMenu, inputYesNo
from ipaddress import ip_address
from os import environ
from src.password_checker.password_abstract import PasswordInput
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.font import init as pg_font_init, get_fonts


def IPValidation(InputText: str):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = gethostbyname(InputText)
		ip_address(address)

	return InputText


AllFonts = get_fonts()


def FontInput(FontName: str, AllFonts=AllFonts):
	"""Will raise an exception if the user enters an invalid font name"""
	assert FontName in AllFonts
	return FontName


SettingsChoices = ['Continue with default settings', 'Customise default font and colour theme for the game']

ThemeChoices = ['Classic theme (dark red board)', 'High contrast theme (orange board)']
ThemeDict = {'Classic theme (dark red board)': 'Classic', 'High contrast theme (orange board)': 'Contrast'}


def UserInputs(
		ThemeChoices=ThemeChoices,
		ThemeDict=ThemeDict,
		SettingsChoices=SettingsChoices,
		AllFonts=AllFonts
):
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
						limit=3
					)

				except:
					print('Defaulting to Times New Roman as you have failed to enter a valid font.')

		if FontChoice:
			BoldFont = inputYesNo(prompt='Would you like that font emboldened by default? ')

		Theme = inputMenu(
			choices=ThemeChoices,
			prompt='Please select the colour theme you would like to play with:\n\n',
			numbered=True
		)
	else:
		Theme = ThemeChoices[0]

	return IP, Port, password, ThemeDict[Theme], FontChoice, (BoldFont == 'yes')
