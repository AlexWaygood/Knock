from __future__ import annotations

from typing import TYPE_CHECKING, overload, List
from collections import UserList
from functools import singledispatchmethod
from src.players.hand_sort_func import SortHand
from itertools import cycle

if TYPE_CHECKING:
	from src.special_knock_types import CardListTypeVar, StringOrInt, PlayerDict, SuitTuple, PlayerList, OptionalSuit,\
		PlayerTypeVar, AnyHand, T, PlayerNameList, AnyCardsIter

	from src.cards.server_card_suit_rank import ServerCard as Card
	from src.cards.server_card_suit_rank import Suit


# @singledispatchmethod decorator is currently buggy; this is a workaround
# (see https://bugs.python.org/issue39679,
# https://stackoverflow.com/questions/62696796/singledispatchmethod-and-class-method-decorators-in-python-3-8)
# noinspection PyMissingTypeHints
def _register(self, cls, method=None):
	if hasattr(cls, '__func__'):
		setattr(cls, '__annotations__', cls.__func__.__annotations__)
	return self.dispatcher.register(cls, func=method)


singledispatchmethod.register = _register


# noinspection PyNestedDecorators
class Player:
	"""Class object for representing a single player in the game."""
	__slots__ = '_name', 'playerindex', 'Hand', 'Bid'

	_AllPlayers: PlayerList = []
	_AllPlayersDict: PlayerDict = {}
	PlayerNo = 0

	def __init__(self, playerindex: int):
		self._name: StringOrInt = playerindex
		self.playerindex = playerindex
		self.Bid = -1
		self.Hand: AnyHand

	@classmethod
	def MakePlayers(cls, n: int):
		cls.PlayerNo = n
		cls._AllPlayers = [cls(i) for i in range(n)]

	@classmethod
	def number(cls) -> int:
		return len(cls._AllPlayers)

	@classmethod
	def first(cls) -> Player:
		return cls._AllPlayers[0]

	@overload
	@classmethod
	def player(cls: PlayerTypeVar, index_or_key: StringOrInt) -> PlayerTypeVar:
		pass

	# the player() method will work whether you supply a player's playerindex or name
	@singledispatchmethod
	@classmethod
	def player(cls, index_or_key: int):
		return cls._AllPlayers[index_or_key]

	@player.register
	@classmethod
	def _(cls, index_or_key: str):
		return cls._AllPlayersDict[index_or_key]

	@classmethod
	def iter(cls: T) -> List[T]:
		return cls._AllPlayers

	@classmethod
	def cycle(cls: T) -> cycle[T]:
		return cycle(cls._AllPlayers)

	@classmethod
	def enumerate(cls: T) -> enumerate:
		return enumerate(cls._AllPlayers)

	@classmethod
	def AllPlayersHaveJoinedTheGame(cls) -> bool:
		return all(isinstance(player.name, str) for player in cls.iter()) and cls.number() == cls.PlayerNo

	@classmethod
	def NewGame(cls) -> None:
		cls.AllPlayers = cls.AllPlayers[1:] + cls.AllPlayers[:1]
		[player.ResetPlayer(cls.PlayerNo) for player in cls.iter()]

	@classmethod
	def reprList(cls) -> PlayerNameList:
		return [repr(player) for player in cls.iter()]

	@property
	def name(self) -> str:
		return self._name

	@name.setter
	def name(self, n: str):
		self._name = n
		self.Hand.playername = n
		self._AllPlayersDict[n] = self

	def ReceiveCards(
			self,
			cards: CardListTypeVar,
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

	# This is kept as a separate method to the classmethod version, as it is extended in players_client.py.
	def ResetPlayer(self, PlayerNo: int):
		self.playerindex = (self.playerindex + 1) if self.playerindex < (PlayerNo - 1) else 0
		return self

	def __repr__(self) -> str:
		return f'{self}. Playerindex: {self.playerindex}. Hand {self.Hand}. Bid: {self.Bid}.'

	def __str__(self) -> str:
		return self.name if isinstance(self.name, str) else f'Player with index {self.playerindex}, as yet unnamed'


class Hand(UserList):
	__slots__ = 'playername'

	def __init__(self) -> None:
		super().__init__()
		self.playername = ''  # Is set when the player's name is set -- see the Player class

	# noinspection PyAttributeOutsideInit
	def NewHand(
			self,
			cards: CardListTypeVar,
			TrumpSuit: Suit
	):
		self.data = cards
		self.sort(TrumpSuit)
		[card.AddToHand(self.playername) for card in self.data]

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
		self.data: CardListTypeVar = SortHand(self.data, TrumpSuit, PlayedSuit=PlayedSuit, SuitTuple=SuitTuple)

	def __getitem__(self, item: StringOrInt):
		try:
			return super().__getitem__(item)
		except IndexError:
			return next(card for card in self.data if repr(card) == item)

	def __iter__(self) -> AnyCardsIter:
		return iter(self.data)
