from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from src.network.network_server import Server
	from src.game.server_game import ServerGame as Game


def startup_sequence() -> tuple[Server, Game, bool]:
	"""Startup sequence for the server script."""

	from src.initialisation.maximise_window import maximise_window
	maximise_window()

	from src.initialisation import print_intro_message, configure_logging
	from src.initialisation.server_initialisation.server_user_inputs import user_inputs

	from src.network.network_server import Server
	from src.game.server_game import ServerGame as Game

	configure_logging(client_side=False)
	print_intro_message()
	number_of_players, bidding_system, password, manually_verify = user_inputs()
	return Server(password), Game(), (manually_verify == 'yes')
