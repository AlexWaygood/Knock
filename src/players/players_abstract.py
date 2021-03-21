from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from collections import UserList
from src.players.hand_sort_func import SortHand

if TYPE_CHECKING:
	from src.special_knock_types import CardList, IndexOrKey, PlayerDict, SuitTuple
	from src.cards.server_card_suit_rank import ServerCard as Card
	from src.cards.server_card_suit_rank import Suit


class Gameplayers(UserList):
	__slots__ = 'Dict'

	def __init__(self):
		super().__init__()
		self.Dict: PlayerDict = {}

	def __getitem__(self, index_or_key: IndexOrKey):
		try:
			return super().__getitem__(index_or_key)
		except:
			return self.Dict[index_or_key]

	def __iter__(self):
		return iter(self.data)

	def __repr__(self):
		return '\n'.join((
			f'Object representing all players in the game, and information about them.',
			'\n'.join([player.ReprInfo() for player in self.data])
		))


class Player(object):
	"""Class object for representing a single player in the game."""
	__slots__ = '_name', 'playerindex', 'Hand', 'Bid'

	AllPlayers: Gameplayers[Player] = Gameplayers()
	PlayerNo = 0

	def __init__(self, playerindex: int):
		self._name = playerindex
		self.playerindex = playerindex
		self.AllPlayers.append(self)
		self.Hand = Hand()
		self.Bid = -1

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, n: str):
		self._name = n
		self.Hand.playername = n
		self.AllPlayers.Dict[n] = self

	@classmethod
	def AllPlayersHaveJoinedTheGame(cls):
		return all(isinstance(player.name, str) for player in cls.AllPlayers) and len(cls.AllPlayers) == cls.PlayerNo

	@classmethod
	def NewGame(cls):
		cls.AllPlayers = cls.AllPlayers[1:] + cls.AllPlayers[:1]

		for player in cls.AllPlayers:
			player.ResetPlayer(cls.PlayerNo)

	def ReceiveCards(
			self,
			cards: CardList,
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

	def ResetPlayer(self, PlayerNo: int):
		self.playerindex = (self.playerindex + 1) if self.playerindex < (PlayerNo - 1) else 0
		return self

	def ReprInfo(self):
		return f'{self!r}. Playerindex: {self.playerindex}. Hand {self.Hand}. Bid: {self.Bid}.'

	def __repr__(self):
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
			cards: CardList,
			TrumpSuit: Suit
	):

		self.data = cards
		self.sort(TrumpSuit)
		self.data = [card.AddToHand(self.playername) for card in self.data]
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
			PlayedSuit: Optional[Suit] = None,
			suit_tuple: SuitTuple = (None, None)
	):
		self.data = SortHand(self.data, TrumpSuit, PlayedSuit=PlayedSuit, SuitTuple=SuitTuple)

	def __getitem__(self, item: IndexOrKey):
		try:
			return super().__getitem__(item)
		except:
			return next(card for card in self.data if repr(card) == item)

	def __iter__(self):
		return iter(self.data)
