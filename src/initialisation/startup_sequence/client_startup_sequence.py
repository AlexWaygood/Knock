import sys
from warnings import filterwarnings
from logging import debug
from os import chdir, environ


def StartupSequence():
	# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
	if getattr(sys, 'frozen', False):
		# noinspection PyUnresolvedReferences,PyProtectedMember
		chdir(sys._MEIPASS)
		filterwarnings("ignore")
		FrozenState = True
	else:
		FrozenState = False

	from src.initialisation.maximise_window import MaximiseWindow

	MaximiseWindow()
	print('Loading modules...')

	from src.initialisation.logging_config import LoggingConfig
	from threading import current_thread

	current_thread().name = 'Display'
	LoggingConfig(True)

	from src.clientside_gameplay import ClientsideGameplay
	from src.game.client_game import ClientGame as Game
	from src.network.network_client import Client

	from src.display.display_manager import DisplayManager
	from src.display.colours import ColourScheme

	from src.initialisation.user_inputs.client_user_inputs import UserInputs
	from src.initialisation.ascii_suits import PrintIntroMessage
	from src.initialisation.client_set_blocked_events import SetBlockedEvents

	environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
	from pygame import init as pg_init
	from pygame.key import set_repeat as set_pg_key_repeat

	PrintIntroMessage()
	pg_init()
	IP, Port, password, Theme, FontChoice, BoldFont = UserInputs()
	StartColour = ColourScheme(Theme).MenuScreen

	if FontChoice:
		from src.display.abstract_text_rendering import Fonts
		Fonts.SetDefaultFont(FontChoice, BoldFont)

	pg_init()
	set_pg_key_repeat(1000, 50)
	SetBlockedEvents()

	debug('Starting Client __init__()')
	client = Client(FrozenState, IP, Port, password)

	debug('Client __init__() finished, receiving message from server')
	Message: str = client.ReceiveQueue.get()
	PlayerNo, playerindex, BiddingSystem = int(Message[0]), int(Message[1]), Message[2:]

	debug('Message from server received, starting Game __init__()')
	Game(BiddingSystem, PlayerNo, FrozenState)

	debug('Game __init__() complete, starting DisplayManager __init__()')
	display_manager = DisplayManager(playerindex, FrozenState, StartColour)

	debug('Finished DisplayManager __init__(), launching ClientsideGameplay __init__().')
	clientside_gameplay = ClientsideGameplay(playerindex)

	return client, clientside_gameplay, display_manager
