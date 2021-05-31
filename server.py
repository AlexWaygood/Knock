#! Python3

"""This script must be run by exactly one machine for a game to take place."""

from src.secret_passwords import SERVER_PORT
from src.initialisation.startup_sequence.server_startup_sequence import StartupSequence
from src.network.server_helper_functions import EternalGameLoop, CommsWithClient
from threading import Thread
from traceback_with_variables import printing_exc

with printing_exc():
	server, game, ManuallyVerify = StartupSequence()

# The server will accept new connections until the expected number of players have connected to the server.
# Remember - this will fail if the server's network router does not have port forwarding set up.
# (Warning does not apply if you are playing within one local area network.)

Thread(name='ServerGameplay', target=EternalGameLoop, daemon=True, args=(game, server)).start()
Thread(name='ClientComms', target=game.ClientCommsLoop, daemon=True).start()

with printing_exc():
	server.Run('127.0.0.1', SERVER_PORT, ManuallyVerify, CommsWithClient, game)
