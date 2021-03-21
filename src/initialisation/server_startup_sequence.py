def StartupSequence():
	from src.initialisation.maximise_window import MaximiseWindow
	MaximiseWindow()

	from src.initialisation.ascii_suits import PrintIntroMessage
	from src.initialisation.server_user_inputs import UserInputs
	from src.initialisation.logging_config import LoggingConfig

	from src.network.network_server import Server, AccessToken
	from src.game.server_game import ServerGame as Game

	LoggingConfig(False)
	PrintIntroMessage()
	NumberOfPlayers, BiddingSystem, password, ManuallyVerify = UserInputs()
	return Server(AccessToken=AccessToken), Game(NumberOfPlayers), BiddingSystem, password, (ManuallyVerify == 'yes')
