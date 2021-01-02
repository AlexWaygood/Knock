"""Two classes to aid communication between the server and clients"""


class Triggers(object):
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


class AttributeTracker(object):
	"""This class holds information about the current state of play"""

	__slots__ = 'StartCardNumber', 'PlayedCards', 'TrumpCard', 'trumpsuit'

	def __init__(self):
		self.StartCardNumber = 0
		self.TrumpCard = None
		self.trumpsuit = ''
		self.PlayedCards = []
