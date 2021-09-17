#! Python3

"""This script must be run by exactly one machine for a game to take place."""

from src.secret_passwords import SERVER_PORT
from src.initialisation.server_initialisation.server_startup_sequence import startup_sequence
from src.network.server_helper_functions import eternal_game_loop, comms_with_client
from threading import Thread
from traceback_with_variables import printing_exc

with printing_exc():
	server, game, manually_verify = startup_sequence()

# The server will accept new connections until the expected number of players have connected to the server.
# Remember - this will fail if the server's network router does not have port forwarding set up.
# (Warning does not apply if you are playing within one local area network.)

Thread(name='ServerGameplay', target=eternal_game_loop, daemon=True, args=(game, server)).start()
Thread(name='ClientComms', target=game.client_comms_loop, daemon=True).start()

with printing_exc():
	server.run('127.0.0.1', SERVER_PORT, manually_verify=manually_verify, comms_function=comms_with_client, game=game)
