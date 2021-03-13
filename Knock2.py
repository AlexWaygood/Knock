import sys
from warnings import filterwarnings


# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
if getattr(sys, 'frozen', False):
	# noinspection PyUnresolvedReferences,PyProtectedMember
	os.chdir(sys._MEIPASS)
	filterwarnings("ignore")


from src.initialisation.maximise_window import MaximiseWindow


MaximiseWindow()
print('Loading modules...')


from threading import Thread
from traceback_with_variables import printing_exc

from src.game.client_game import ClientGame as Game
from src.clientside_gameplay.gameplay import Play
from src.clientside_gameplay.event_loop import GameplayLoop
from src.network.client_class import Client
from src.display.display_manager import DisplayManager
from src.initialisation.initialisation import PrintIntroMessage

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import init
from pygame.time import Clock


IP, Port, password, Theme = PrintIntroMessage()


init()
clock = Clock()
client = Client(IP, Port, password)
Message = client.ReceiveQueue.get()
PlayerNo, playerindex, BiddingSystem = int(Message[0]), int(Message[1]), Message[2:]
game = Game(PlayerNo)
player = game.gameplayers[playerindex]
dM = DisplayManager(Theme, game, player)

gamesurf, context, userInput, mouse, typewriter, errors = dM.GetAttributes((
	'GameSurf', 'InputContext', 'UserInput', 'Mouse', 'Typewriter', 'Errors'
))

scrollwheel = mouse.Scrollwheel

Thread(target=Play, args=(game, context, typewriter, player, client, BiddingSystem, dM)).start()
Thread(target=game.UpdateLoop, args=(context, client, player)).start()

with printing_exc():
	while True:
		GameplayLoop(clock, game, client, dM, mouse, gamesurf, context, userInput, scrollwheel, errors, player)
