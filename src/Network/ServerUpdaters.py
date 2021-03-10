from src.DataStructures import DictLike

"""Two classes to aid communication between the server and clients"""


class Triggers(DictLike):
	"""

	This class holds data for the server to communicate with the clients...
	 ...when the clients are free to move on to the next part of the game.

	 """

	__slots__ = 'Events', 'Surfaces'

	def __init__(self):
		self.Events = {
			'GameInitialisation': 0,
			'RoundStart': 0,
			'NewPack': 0,
			'CardsDealt': 0,
			'TrickStart': 0,
			'TrickWinnerLogged': 0,
			'TrickEnd': 0,
			'RoundEnd': 0,
			'PointsAwarded': 0,
			'WinnersAnnounced': 0,
			'TournamentLeaders': 0,
			'NewGameReset': 0,
			'StartNumberSet': 0
		}

		self.Surfaces = {
			'Scoreboard': 0,
			'TrumpCard': 0,
			'Hand': 0,
			'Board': 0,
		}

	def __eq__(self, other):
		return self.Events == other.Events and self.Surfaces == other.Surfaces


class DoubleTrigger(object):
	__slots__ = 'Client', 'Server'

	def __init__(self):
		self.Client = Triggers()
		self.Server = Triggers()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return True
