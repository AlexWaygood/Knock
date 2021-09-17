"""Startup sequnce on the clientside."""

from __future__ import annotations
from typing import TYPE_CHECKING
from logging import debug

from src import DocumentedIntConstants, config
import src.config as rc
from src.static_constants import FillColours

if TYPE_CHECKING:
	from src.network.network_client import Client
	from src.display import DisplayManager


class PygameKeyEventConstants(DocumentedIntConstants):
	"""Two constants relating to pygame key-event settings."""

	KEY_EVENT_DELAY = 1000, "The number of milliseconds a key must be held down before it registers as a repeated event"
	KEY_EVENT_FREQUENCY = 50, "The interval, in milliseconds, between each key event when a key is being held down"


def do_pygame_startup() -> None:
	"""Startup pygame."""

	# Suppress the annoying message that comes up on the screen whenever you import pygame.
	from os import environ
	environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

	from pygame import init as initialise_pygame
	from pygame.display import init as initialise_pygame_display
	from pygame.key import set_repeat as set_pygame_key_repeat
	from src.initialisation.client_initialisation import set_pygame_blocked_events

	initialise_pygame()
	initialise_pygame_display()
	set_pygame_key_repeat(PygameKeyEventConstants.KEY_EVENT_DELAY, PygameKeyEventConstants.KEY_EVENT_FREQUENCY)
	set_pygame_blocked_events()


def startup_sequence() -> tuple[Client, DisplayManager]:
	"""Startup sequence on the clientside"""

	config.determine_if_we_are_compiled()

	from src.initialisation import maximise_window, configure_logging, print_intro_message

	maximise_window()
	print('Loading modules...')

	from threading import current_thread

	current_thread().name = 'Display'

	configure_logging(client_side=True)
	debug('\n\nNEW RUN OF PROGRAMME STARTING\n\n')

	# Determine some of the display dimensions at game opening.
	# This HAS to be done before any module imports src.cards.client_card.
	# The Game module imports src.cards.client_card.
	screen_size = config.get_screen_size()
	config.get_game_dimensions(window_dimensions=screen_size)

	from src.game.client_game import ClientGame as Game
	from src.network.network_client import Client

	from src.display import DisplayManager, THEMES, ColourScheme, Fonts

	from src.initialisation.client_initialisation import user_inputs, FontConstants

	print_intro_message()
	ip_addr, port, password, theme, font_choice, bold_font = user_inputs(THEMES)
	start_colour = ColourScheme(theme)[FillColours.MENU_SCREEN_FILL_COLOUR]

	if font_choice is not FontConstants.NO_FONT_SELECTED:
		Fonts.set_default_font(font_choice, bold_font=bold_font)

	debug('Starting Client __init__()')
	rc.client = client = Client(ip_addr, port, password)

	debug('Client __init__() finished, receiving message from server')
	message: str = client.receive_queue.get()
	rc.player_number, rc.playerindex, rc.bidding_system = int(message[0]), int(message[1]), message[2:]

	debug('message from server received, starting Game __init__()')
	rc.game = Game()

	do_pygame_startup()

	debug('Game __init__() full_message_received, starting DisplayManager __init__()')
	rc.display_manager = display_manager = DisplayManager(start_colour=start_colour)

	debug('Finished DisplayManager __init__().')

	return client, display_manager
