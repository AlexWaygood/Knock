from __future__ import annotations

from typing import TYPE_CHECKING, overload
from collections import UserList
from functools import singledispatchmethod
from src.players.hand_sort_func import SortHand
from itertools import cycle

if TYPE_CHECKING:
	from src.special_knock_types import AnyCardList, IndexOrKey, PlayerDict, SuitTuple, PlayerList, OptionalSuit
	from src.cards.server_card_suit_rank import ServerCard as Card
	from src.cards.server_card_suit_rank import Suit
	from src.players.players_client import ClientPlayer
	from src.players.players_server import ServerPlayer


# noinspection PyNestedDecorators
class Player(object):
	"""Class object for representing a single player in the game."""
	__slots__ = '_name', 'playerindex', 'Hand', 'Bid'

	_AllPlayers: PlayerList = []
	_AllPlayersDict: PlayerDict = {}
	PlayerNo = 0

	def __init__(self, playerindex: int):
		self._name = playerindex
		self.playerindex = playerindex
		self.AllPlayers.append(self)
		self.Hand = Hand()
		self.Bid = -1

	@classmethod
	def SetNumber(cls, n: int):
		cls.PlayerNo = n

	@classmethod
	def number(cls):
		return len(cls._AllPlayers)

	@classmethod
	def first(cls):
		return cls._AllPlayers[0]

	### 3 overloaded methods for player() -- the return type depends on whether it's an inherited class or not.
	### As a result, the type-hinting is quite complex

	@overload
	@classmethod
	def player(cls: Player, index_or_key: IndexOrKey) -> Player:
		pass

	@overload
	@classmethod
	def player(cls: ClientPlayer, index_or_key: IndexOrKey) -> ClientPlayer:
		pass

	@overload
	@classmethod
	def player(cls: ServerPlayer, index_or_key: IndexOrKey) -> ServerPlayer:
		pass

	### the player() method will work whether you supply a player's playerindex or name

	@singledispatchmethod
	@classmethod
	def player(cls, index_or_key: int):
		return cls._AllPlayers[index_or_key]

	@player.register
	@classmethod
	def _(cls, index_or_key: str):
		return cls._AllPlayersDict[index_or_key]

	###

	@classmethod
	def iter(cls):
		return iter(cls._AllPlayers)

	@classmethod
	def cycle(cls):
		return cycle(cls._AllPlayers)

	@classmethod
	def enumerate(cls):
		return enumerate(cls._AllPlayers)

	@classmethod
	def AllPlayersHaveJoinedTheGame(cls):
		return all(isinstance(player.name, str) for player in cls.iter()) and cls.number() == cls.PlayerNo

	@classmethod
	def NewGame(cls):
		cls.AllPlayers = cls.AllPlayers[1:] + cls.AllPlayers[:1]

		for player in cls.iter():
			player.ResetPlayer(cls.PlayerNo)

	@classmethod
	def reprList(cls):
		return [repr(player) for player in cls.iter()]

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, n: str):
		self._name = n
		self.Hand.playername = n
		self._AllPlayersDict[n] = self

	def ReceiveCards(
			self,
			cards: AnyCardList,
			TrumpSuit: Suit
	):

		# Must receive an argument in the form of a list
		self.Hand.NewHand(cards, TrumpSuit)
		return self

	def PlayCard(
			self,
			card: Card,
			TrumpSuit: Suit
	):

		self.Hand.RemoveCard(card, TrumpSuit)
		self.Hand.Iteration += 1

	# This is kept as a separate method to the classmethod version, as it is extended in players_client.py.
	def ResetPlayer(self, PlayerNo: int):
		self.playerindex = (self.playerindex + 1) if self.playerindex < (PlayerNo - 1) else 0
		return self

	def __repr__(self):
		return f'{self}. Playerindex: {self.playerindex}. Hand {self.Hand}. Bid: {self.Bid}.'

	def __str__(self):
		return self.name if isinstance(self.name, str) else f'Player with index {self.playerindex}, as yet unnamed'

	def __eq__(self, other: object):
		assert isinstance(other, Player), "Can't compare a player with a non-player object"
		return self.name == other.name and self.Hand.Iteration == other.Hand.Iteration


class Hand(UserList):
	__slots__ = 'Iteration', 'playername'

	def __init__(self):
		super().__init__()
		self.Iteration = 0
		self.playername = ''  # Is set when the player's name is set -- see the Player class

	# noinspection PyAttributeOutsideInit
	def NewHand(
			self,
			cards: AnyCardList,
			TrumpSuit: Suit
	):

		self.data = cards
		self.sort(TrumpSuit)
		self.data: AnyCardList = [card.AddToHand(self.playername) for card in self.data]
		self.Iteration += 1

	def RemoveCard(
			self,
			card: Card,
			TrumpSuit: Suit
	):
		suitTuple = (self.data[0].Suit, self.data[-1].Suit)
		self.data.remove(card)
		self.sort(TrumpSuit, PlayedSuit=card.Suit, suit_tuple=suitTuple)

	def sort(
			self,
			TrumpSuit: Suit,
			PlayedSuit: OptionalSuit = None,
			suit_tuple: SuitTuple = (None, None)
	):
		self.data: AnyCardList = SortHand(self.data, TrumpSuit, PlayedSuit=PlayedSuit, SuitTuple=SuitTuple)

	# Used in gamesurf.py
	def MoveColliderects(
			self,
			XMotion: float,
			YMotion: float
	):
		for card in self.data:
			card.colliderect.move_ip(XMotion, YMotion)

	def __getitem__(self, item: IndexOrKey):
		try:
			return super().__getitem__(item)
		except:
			return next(card for card in self.data if repr(card) == item)

	def __iter__(self):
		return iter(self.data)
