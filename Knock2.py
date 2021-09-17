#! Python3

"""This is the client-side script, that should be run by each player who wants to take part in the game."""

from threading import Thread
from traceback_with_variables import printing_exc
from src.initialisation.client_initialisation.client_startup_sequence import startup_sequence
from src.clientside_gameplay import play


with printing_exc():
	client, display_manager = startup_sequence()

# One thread for encoding the order of gameplay according to the rules of Knock.
Thread(name='Gameplay', target=play).start()

# One thread for receiving messages from the server.
Thread(name='ServerComms', target=client.run).start()

# The main thread deals with all things relevant to pygame display.
with printing_exc():
	display_manager.run()
