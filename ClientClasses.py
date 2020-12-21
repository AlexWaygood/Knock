"""A smattering of short classes and functions to make the Client script cleaner."""

from Player import Player
from ipaddress import ip_address
import socket
from itertools import groupby


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
			'CurrentBoard': 0,
		}


class AttributeTracker(object):
	"""This class holds information about the current state of play"""

	__slots__ = 'Tournament', 'StartCardNumber', 'Round', 'Trick', 'Errors'

	def __init__(self, server=False, PlayerNumber=0):
		self.Tournament = {
			'GamesPlayed': 0,
			'PlayerNumber': PlayerNumber,
			'MaxCardNumber': (51 // PlayerNumber) if server else 0,
			'gameplayers': Player.AllPlayers if server else []
		}

		self.StartCardNumber = 0

		self.Round = {
			'PackOfCards': [],
			'TrumpCard': None,
			'trumpsuit': '',
			'CardNumberThisRound': 0,
			'RoundNumber': 1
		}

		self.Trick = {
			'PlayedCards': [],
			'Winner': None,
			'TrickInProgress': False,
			'TrickNumber': 0,
			'WhoseTurnPlayerIndex': -1
		}


class SurfaceAndPosition(object):
	"""Class for holding data about various surfaces that will be used frequently in the game"""

	__slots__ = 'surf', 'pos', 'surfandpos', 'RectList', 'midpoint'

	def __init__(self, surface, position, RectList=None, Dimensions=(0, 0)):
		self.surf = surface
		self.pos = position
		self.surfandpos = (surface, position)
		self.RectList = RectList
		self.midpoint = Dimensions[0] // 2

	def fill(self, *args):
		self.surf.fill(*args)

	def blit(self, *args):
		self.surf.blit(*args)

	def blits(self, *args):
		self.surf.blits(*args)

	def AddSurf(self, surf):
		self.surf = surf
		self.surfandpos = (surf, self.pos)


class FontAndLinesize(object):
	"""Class for holding data about various fonts that will be used frequently in the game"""

	__slots__ = 'font', 'linesize'

	def __init__(self, font):
		self.font = font
		self.linesize = font.get_linesize()

	def render(self, *args):
		return self.font.render(*args)

	def size(self, text):
		return self.font.size(text)


def IPValidation(InputText):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = socket.gethostbyname(InputText)
		ip_address(address)

	return InputText


def AllEqual(Iterable):
	"""Does what it says on the tin"""

	g = groupby(Iterable)
	return next(g, True) and not next(g, False)
