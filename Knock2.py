from __future__ import annotations
import sys
from warnings import filterwarnings
from os import environ, chdir


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

from logging import debug
from threading import Thread, current_thread
from traceback_with_variables import printing_exc
from typing import TYPE_CHECKING

from src.clientside_gameplay.gameplay import Play
from src.clientside_gameplay.event_loop import GameplayLoop

from src.game.client_game import ClientGame as Game
from src.network.client_class import Client
from src.display.display_manager import DisplayManager
from src.display.colour_scheme import ColourScheme

from src.initialisation.logging_config import LoggingConfig
from src.initialisation.client_user_inputs import UserInputs
from src.initialisation.ascii_suits import PrintIntroMessage
from src.initialisation.set_blocked_events import SetBlockedEvents

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import init as pg_init
from pygame.time import Clock
from pygame.key import set_repeat as set_pg_key_repeat

if TYPE_CHECKING:
	from src.players.players_client import ClientPlayer as Player
	from src.display.mouse.mouse import Scrollwheel


current_thread().name = 'Display'
LoggingConfig(True)
debug('\n\nNEW RUN OF PROGRAMME STARTING\n\n')

PrintIntroMessage()
IP, Port, password, Theme = UserInputs()
ColourScheme(Theme)

pg_init()
set_pg_key_repeat(1000, 50)
SetBlockedEvents()

clock = Clock()
client = Client(FrozenState, IP, Port, password)
Message: str = client.ReceiveQueue.get()
PlayerNo, playerindex, BiddingSystem = int(Message[0]), int(Message[1]), Message[2:]
game = Game(PlayerNo, FrozenState)
player: Player = game.gameplayers[playerindex]

debug('Starting DisplayManager __init__()')
dM = DisplayManager(player, FrozenState)
debug('Finished DisplayManager __init__().')

gamesurf, context, userInput, mouse, typewriter, errors, scoreboard = dM.GetAttributes((
	'GameSurf', 'InputContext', 'UserInput', 'Mouse', 'Typewriter', 'Errors', 'InteractiveScoreboard'
))

scrollwheel: Scrollwheel = mouse.Scrollwheel

debug('Launching gameplay thread and server-comms threads.')

Thread(target=Play, name='Gameplay', args=(game, context, typewriter, player, client, BiddingSystem, dM)).start()
Thread(target=game.UpdateLoop, name='ServerComms', args=(context, player)).start()

with printing_exc():
	debug('Starting main pygame loop.')

	while True:
		GameplayLoop(clock, game, client, dM, mouse, gamesurf, context, userInput, scrollwheel, errors, player, scoreboard)
