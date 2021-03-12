import sys
from warnings import filterwarnings


# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
if getattr(sys, 'frozen', False):
	# noinspection PyUnresolvedReferences,PyProtectedMember
	os.chdir(sys._MEIPASS)
	filterwarnings("ignore")


from src.Initialisation.MaximiseWindow import MaximiseWindow


MaximiseWindow()
print('Loading modules...')


from threading import Thread
from traceback_with_variables import printing_exc

from src.Game.ClientGame import ClientGame as Game
from src.ClientsideGameplay.Gameplay import Play
from src.ClientsideGameplay.EventLoop import GameplayLoop
from src.Network.ClientClass import Client
from src.Display.DisplayManager import DisplayManager
from src.Initialisation.Initialisation import PrintIntroMessage

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import init
from pygame.time import Clock


IP, Port, password, Theme = PrintIntroMessage()


init()
clock = Clock()
client = Client(IP, Port, password)
Message = client.ReceiveQueue.get()
print(f'Line 42 of Knock2: Message received is {Message}.')
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
