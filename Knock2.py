#! Python3

"""This is the client-side script, that should be run by each player who wants to take part in the game."""

from threading import Thread
from traceback_with_variables import printing_exc
from src.initialisation.startup_sequence.client_startup_sequence import StartupSequence


with printing_exc():
	client, clientside_gameplay, display_manager = StartupSequence()

# One thread for encoding the order of gameplay according to the rules of Knock.
Thread(name='Gameplay', target=clientside_gameplay.Play).start()

# One thread for receiving messages from the server.
Thread(name='ServerComms', target=client.UpdateLoop, args=(display_manager.InputContext,)).start()

# The main thread deals with all things relevant to pygame display.
with printing_exc():
	display_manager.Run()
