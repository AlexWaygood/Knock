"""Present the user with a variety of input options before the name begins."""

from __future__ import annotations
from typing import TYPE_CHECKING, NamedTuple, Final, Annotated, Union
from socket import gethostbyname
from pprint import pprint
from pyinputplus import inputCustom, inputMenu, inputYesNo, RetryLimitException
from ipaddress import ip_address
from getpass import getpass
from enum import Enum
from aenum import NamedConstant, constant
from random import random

from src.password_checker.password_abstract import validate_inputted_password, IncorrectPasswordLengthException

from pygame.font import (
	get_fonts,
	init as initialise_pygame_fonts
)

if TYPE_CHECKING:
	from src.special_knock_types import ThemeTuple


class DisplayCustomisationOptions(str, Enum):
	"""A clientside user can either proceed with the default settings, or customise certain display options."""

	DEFAULT_SETTINGS = 'Continue with default settings'
	CUSTOM_SETTINGS = 'Customise default font and colour theme for the game'


# This needs to be done before `FontConstants` is defined.
initialise_pygame_fonts()


class FontConstants(NamedConstant):
	"""Several constants relating to the method by which a client may choose a font."""

	ALL_FONTS = constant(tuple(get_fonts()), doc="A tuple of all system fonts that are available")
	NO_FONT_SELECTED = constant(random(), doc="Placeholder showing a font wasn't selected by the user.")
	ENTRY_MAX_ATTEMPTS = constant(3, doc="How many times a user can attempt to input a font name.")


DEFAULT_THEME_INDEX: Final = 0

FontSelectionChoiceType = Annotated[
	Union[str, FontConstants],
	'Either a font name (a `str`), or `NO_FONT_SELECTED`, signifying the user is happy with the default font.'
]


def validate_ip_address(ip_address_string: str) -> str:
	"""Raise an exception if the user has not entered a valid IP or hostname to connect to."""

	# noinspection PyBroadException
	try:
		ip_address(ip_address_string)
	except BaseException:
		address = gethostbyname(ip_address_string)
		ip_address(address)

	return ip_address_string


def password_input() -> str:
	"""Ask the client to input the password for the game, validate the password, return it as a string."""

	while True:
		password = getpass(
			prompt=(
				'Please enter the password to connect to this game, if one has been set '
				'(press Enter if none has been set): '
			)
		)

		try:
			validate_inputted_password(password)
		except IncorrectPasswordLengthException as err:
			print(err)
		else:
			return password


def client_wishes_to_customise_display_options() -> bool:
	"""Return `True` if the client wants to customise display options for the game, else `False`."""

	settings_choice = inputMenu(
		choices=tuple(DisplayCustomisationOptions),
		prompt=(
			'Select whether you would like to continue with default display settings, '
			'or customise the font and colours'
			'(press enter to continue with default settings):\n\n'
		),
		numbered=True,
		blank=True
	)

	customisation_desired: bool = (settings_choice is DisplayCustomisationOptions.CUSTOM_SETTINGS)
	return customisation_desired


def font_customisation_input() -> FontSelectionChoiceType:
	"""Return the name of the client's desired font, or `NO_FONT_SELECTED` if they wish to use the default font."""

	font_choice = input(
		'Please enter your preferred font for the game (press enter to default to Times New Roman):\n\n'
	)

	return font_choice if font_choice else FontConstants.NO_FONT_SELECTED


def client_wishes_to_view_available_fonts(desired_font: str) -> bool:
	"""Return `True` if the client wishes to view all available fonts, else `False`."""

	view_available_fonts = inputYesNo(
		f'{desired_font} is not a valid font. '
		f'Would you like to see a list of all available fonts on your machine? '
	)

	return view_available_fonts == 'yes'


def raise_for_invalid_font(font_name: str) -> str:
	"""Raise an exception if the user has entered an invalid font name."""

	if font_name not in FontConstants.ALL_FONTS:
		raise ValueError('The font you have selected is sadly not available.')
	return font_name


def ask_for_valid_font_selection_inner() -> FontSelectionChoiceType:
	"""Ask the user which font they would like, and validate that the selected font is available.
	If the user repeatedly makes an invalid choice, `RetryLimitException` will be raised.

	Returns
	-------
	Either a string (the name of the desired font), or `NO_FONT_SELECTED`,
	in which case the programme will default to the default font.
	"""

	selected_font = inputCustom(
		raise_for_invalid_font,
		prompt='Please enter your preferred font for the game (press enter to default to Times New Roman):\n\n',
		blank=True,
		limit=FontConstants.ENTRY_MAX_ATTEMPTS
	)

	return selected_font if selected_font else FontConstants.NO_FONT_SELECTED


def ask_for_valid_font_selection() -> FontSelectionChoiceType:
	"""Ask the user for their desired font selection,
	and return `NO_FONT_SELECTED` if they repeatedly fail to make a valid choice.

	Returns
	-------
	Either a string (the name of the desired font), or `NO_FONT_SELECTED`,
	in which case the programme will default to the default font.
	"""

	try:
		selected_font = ask_for_valid_font_selection_inner()
	except RetryLimitException:
		print('Defaulting to Times New Roman as you have failed to enter a valid font.')
		selected_font = FontConstants.NO_FONT_SELECTED

	return selected_font


def validate_font(desired_font: str) -> FontSelectionChoiceType:
	"""Validate that the user's desired font is available, and repeatedly ask them for a valid selection if not.
	Return the user's desired font, or `NO_FONT_SELECTED` to signify that the default font should be used.
	"""

	if desired_font in FontConstants.ALL_FONTS:
		selected_font = desired_font
	else:
		if client_wishes_to_view_available_fonts(desired_font):
			pprint(get_fonts())

		selected_font = ask_for_valid_font_selection()

	return selected_font


def client_wants_bold_font() -> bool:
	"""Return `True` if the client wants bold fonts by default, else `False`"""
	return inputYesNo(prompt='Would you like that font emboldened by default? ') == 'yes'


def theme_selection(themes: ThemeTuple) -> Annotated[str, "The client's desired colour theme'"]:
	"""Present the client with an array of possible colour themes, return the desired option."""

	return inputMenu(
		choices=[t.description for t in themes],
		prompt='Please select the colour theme you would like to play with:\n\n',
		numbered=True
	)


class DisplayCustomisationChoices(NamedTuple):
	"""A `NamedTuple` detailing the display customisation selections made by the client.
	The return type of the `display_customisation_choices` function below.
	"""

	desired_font: FontSelectionChoiceType
	bold_font_desired: bool
	selected_theme: str


def display_customisation_choices(themes: ThemeTuple) -> DisplayCustomisationChoices:
	"""Present the client with an array of display options, return a `NamedTuple` detailing those options.

	This function is only called in the event that the client has already stated
	that they wish to customise the display options.
	"""

	desired_font: FontSelectionChoiceType = FontConstants.NO_FONT_SELECTED
	bold_font_desired = False

	font_customisation_choice = font_customisation_input()

	if font_customisation_choice is not FontConstants.NO_FONT_SELECTED:
		desired_font = validate_font(font_customisation_choice)

		if desired_font is not FontConstants.NO_FONT_SELECTED:
			bold_font_desired = client_wants_bold_font()

	selected_theme = theme_selection(themes)

	return DisplayCustomisationChoices(
		desired_font=desired_font,
		bold_font_desired=bold_font_desired,
		selected_theme=selected_theme
	)


class ClientUserInputs(NamedTuple):
	"""A `NamedTuple` detailing an array of input choices presented to a client prior to starting the game.
	The return type of the `user_inputs` function.
	"""

	IP: str
	port: int
	password: str
	selected_theme: str
	selected_font: FontSelectionChoiceType
	bold_font_desired: bool


def user_inputs(themes: ThemeTuple) -> ClientUserInputs:
	"""Ask the client for an array of inputs prior to starting the game, return a `NamedTuple` detailing the choices."""

	# IP = 'alexknockparty.mywire.org'

	# noinspection PyPep8Naming
	ip_addr = '127.0.0.1'
	print('Connecting to local host.')
	port = 5555

	# IP = inputCustom(
	#   validate_ip_address,
	#   'Please enter the IP address or hostname of the server you want to connect to: '
	# )

	# Port = inputInt('Please enter which port you wish to connect to: ', min=5000, max=65535)

	password = password_input()

	# noinspection PyPep8Naming
	DEFAULT_THEME = themes[DEFAULT_THEME_INDEX].description

	display_customisation_desired: bool = client_wishes_to_customise_display_options()

	if display_customisation_desired:
		desired_font, bold_font_desired, selected_theme = display_customisation_choices(themes)
	else:
		desired_font, bold_font_desired, selected_theme = FontConstants.NO_FONT_SELECTED, False, DEFAULT_THEME

	return ClientUserInputs(
		IP=ip_addr,
		port=port,
		password=password,
		selected_theme=selected_theme,
		selected_font=desired_font,
		bold_font_desired=bold_font_desired
	)
