from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from src.special_knock_types import ServerStartUpReturnables


def StartupSequence() -> ServerStartUpReturnables:
	from src.initialisation.maximise_window import MaximiseWindow
	MaximiseWindow()

	from src.initialisation.ascii_suits import PrintIntroMessage
	from src.initialisation.user_inputs.server_user_inputs import UserInputs
	from src.initialisation.logging_config import LoggingConfig

	from src.network.network_server import Server
	from src.game.server_game import ServerGame as Game

	LoggingConfig(False)
	PrintIntroMessage()
	NumberOfPlayers, BiddingSystem, password, ManuallyVerify = UserInputs()
	return Server(password), Game(BiddingSystem, NumberOfPlayers), (ManuallyVerify == 'yes')
