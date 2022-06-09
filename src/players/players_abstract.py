"""A class representing a player in the game.

The `Players` class in this module is not actually instantiated directly.
Instead, it is used as a base class for the `ServerPlayers` and `ClientPlayers` classes.

Also included in this module is a metaclass to support the `Players` class.
"""

from __future__ import annotations

from typing import Iterator, TypeVar, cast, Optional, Final, Sequence, Iterable, Literal, Union
from types import MappingProxyType

import src.config as rc
from src import DocumentedMetaclassMixin, DataclassyReprBase, IntEnumNiceStr, DocumentedPlaceholders
from src.utils.sequence_proxy import SequenceProxy
from src.cards import Suit
from src.cards.abstract_card import AbstractCard


class Bid(IntEnumNiceStr):
	"""An enumeration of all possible bids a player might make."""

	ZERO = 0
	ONE = 1
	TWO = 2
	THREE = 3
	FOUR = 4
	FIVE = 5
	SIX = 6
	SEVEN = 7
	EIGHT = 8
	NINE = 9
	TEN = 10
	ELEVEN = 11
	TWELVE = 12
	THIRTEEN = 13


ValidBid = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
PlayerIndex = Literal[0, 1, 2, 3, 4, 5]
NumberOfPlayers = Literal[2, 3, 4, 5, 6]
PossibleLengthOfPlayersList = Literal[0, 1, 2, 3, 4, 5, 6]


class Placeholders(DocumentedPlaceholders):
	"""Placeholders for the `players` module."""

	NOT_YET_NAMED = "Placeholder for when a player has not yet been named."
	NOT_YET_BID = "Placeholder for when a player has not yet bid."


# noinspection PyTypeChecker
P = TypeVar('P', bound='AbstractPlayers')
# noinspection PyTypeChecker
H = TypeVar('H', bound='hand[Any]')
# noinspection PyTypeChecker
PM = TypeVar('PM', bound='PlayersMeta')


# Useful for testing purposes to have a custom exception type.
class InvalidPlayerindexException(IndexError):
	"""Raised when a player enters an invalid player_index to `PlayersMeta.__call__`"""


class InvalidNameException(ValueError):
	"""Raised when a player attempts to enter an invalid name."""


# noinspection PyPropertyDefinition,PyMethodParameters
class PlayersMeta(DocumentedMetaclassMixin):
	"""Metaclass for the `Players` class"""

	# noinspection PyUnresolvedReferences
	_all_players_list: Final[list['AbstractPlayers']] = []
	# noinspection PyUnresolvedReferences
	_all_players_list_proxy: Final[SequenceProxy['AbstractPlayers']] = SequenceProxy(_all_players_list)

	@property
	def all_players_sequence(cls: type[P], /) -> SequenceProxy[P]:
		# noinspection PyUnresolvedReferences
		"""Get a read-only "view" of the current list of all players.

		Since this is defined in the metaclass, this property can only be accessed on the class,
		not an instance of the class.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=3)
		>>> AbstractPlayers.all_players_sequence
		SequenceProxy([])
		>>> print(AbstractPlayers.all_players_sequence)
		[]
		>>> AbstractPlayers.all_players_sequence = ['foo', 'bar']
		Traceback (most recent call last):
		AttributeError: can't set attribute
		>>> AbstractPlayers.all_players_sequence.append('foo')
		Traceback (most recent call last):
		AttributeError: 'SequenceProxy' object has no attribute 'append'
		>>> p = AbstractPlayer()
		>>> len(AbstractPlayers.all_players_sequence)
		1
		>>> AbstractPlayers.all_players_sequence[0] is p
		True
		>>> AbstractPlayers.all_players_sequence[0] = 'foo'
		Traceback (most recent call last):
		TypeError: 'SequenceProxy' object does not support item assignment
		>>> p.all_players_sequence
		Traceback (most recent call last):
		AttributeError: 'AbstractPlayer' object has no attribute 'all_players_sequence'
		"""

		return cls._all_players_list_proxy

	# noinspection PyUnresolvedReferences
	_all_players_dict: Final[dict[str, 'AbstractPlayers']] = {}
	# noinspection PyUnresolvedReferences
	_all_players_dict_proxy: Final[MappingProxyType[str, 'AbstractPlayers']] = MappingProxyType(_all_players_dict)

	@property
	def all_players_mapping(cls: type[P], /) -> MappingProxyType[str, P]:
		# noinspection PyUnresolvedReferences
		"""Get a read-only mapping of playernames-to-players.

		Since this is defined in the metaclass, this property can only be accessed on the class,
		not an instance of the class.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=3)
		>>> AbstractPlayers.all_players_mapping
		mappingproxy({})
		>>> print(AbstractPlayers.all_players_mapping)
		{}
		>>> AbstractPlayers.all_players_mapping = {'foo': 'bar'}
		Traceback (most recent call last):
		AttributeError: can't set attribute
		>>> AbstractPlayers.all_players_mapping.update({'foo': 'bar'})
		Traceback (most recent call last):
		AttributeError: 'mappingproxy' object has no attribute 'update'
		>>> p = AbstractPlayer()
		>>> p.name = 'Alex'
		>>> len(AbstractPlayers.all_players_mapping)
		1
		>>> AbstractPlayers.all_players_mapping['Alex'] is p
		True
		>>> AbstractPlayers.all_players_mapping['Alex'] = 'foo'
		Traceback (most recent call last):
		TypeError: 'mappingproxy' object does not support item assignment
		>>> p.all_players_mapping
		Traceback (most recent call last):
		AttributeError: 'AbstractPlayer' object has no attribute 'all_players_mapping'
		"""

		return cls._all_players_dict_proxy

	def reset_for_unit_test(cls, /, *, player_number: NumberOfPlayers) -> None:
		"""Clear the list and mapping of players, reset the PLAYER_NUMBER constant, deabstractify any abstractmethods.
		(Convenience function for testing purposes.)
		"""

		cls._all_players_list.clear()
		cls._all_players_dict.clear()
		rc.player_number = player_number

	def make_players(cls: type[P], /, *, names: Optional[Iterable[str]] = None) -> SequenceProxy[P]:
		# noinspection PyUnresolvedReferences,PyShadowingNames
		"""Generate a list of `Players` objects at the start of the game, and return an iterable sequence of all players.
		The returned sequence of `Player` objects is a read-only `SequenceProxy` object.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> len(AbstractPlayers.make_players()) == len(AbstractPlayers) == 2
		True
		>>> for player in AbstractPlayers:
		...     print(f'Player {player.player_index}: {player.name}')
		...
		Player 0: <NOT_YET_NAMED>
		Player 1: <NOT_YET_NAMED>
		"""

		# Players are appended to the `_all_players_list` in `PlayerMeta.__call__`
		for _ in range(rc.player_number):
			cls()

		if names is not None:
			for player, name in zip(cls, names):
				player.name = name

		return cls.all_players_sequence

	def add_player_to_dict(cls: type[P], /, *, player: P, name: str) -> None:
		# noinspection PyUnresolvedReferences
		"""add the player to the dictionary mapping players' player_names to `Players` objects

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p = AbstractPlayer()
		>>> p._name = 'Alex'
		>>> AbstractPlayers.all_players_mapping
		mappingproxy({})
		>>> AbstractPlayers.add_player_to_dict(player=p, name='Alex')
		>>> AbstractPlayers.all_players_mapping['Alex'] is p
		True
		"""

		cls._all_players_dict[name] = player

	def end_of_game(cls, /) -> None:
		# noinspection PyUnresolvedReferences
		"""Reset all `Players` objects at the end of the game, in prepraration for the next game.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=3)
		>>> p0, p1, p2 = AbstractPlayers.make_players()
		>>> [p.player_index for p in AbstractPlayers]
		[0, 1, 2]
		>>> [p0.player_index, p1.player_index, p2.player_index]
		[0, 1, 2]
		>>> AbstractPlayers.end_of_game()
		>>> [p.player_index for p in AbstractPlayers]
		[0, 1, 2]
		>>> [p0.player_index, p1.player_index, p2.player_index]
		[2, 0, 1]
		"""

		cls._all_players_list.append(cls._all_players_list.pop(0))

	@property
	def all_players_named(cls, /) -> bool:
		"""A boolean value: `True` if all players have been named, else `False`.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> len(AbstractPlayers.make_players())
		2
		>>> AbstractPlayer.all_players_named
		False
		>>> AbstractPlayer(0).name = 'Alex'
		>>> AbstractPlayers.all_players_named
		False
		>>> AbstractPlayer(1).name = 'Charlotte'
		>>> AbstractPlayers.all_players_named
		True
		"""
		return all(player.has_been_named for player in cls)

	@property
	def names(cls, /) -> list[str]:
		"""Get a `list` of strings representing the names of all players.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> len(AbstractPlayers.make_players(names=('Alex', 'Charlotte')))
		2
		>>> AbstractPlayers.names
		['Alex', 'Charlotte']
		"""
		return [player.name for player in cls]

	@property
	def all_bid(cls, /) -> bool:
		"""A boolean value: `True` if all players have bid this round, else `False`.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> len(AbstractPlayers.make_players())
		2
		>>> AbstractPlayers.all_bid
		False
		>>> AbstractPlayer(0).bids(2)
		>>> AbstractPlayers.all_bid
		False
		>>> AbstractPlayer(1).bids(3)
		>>> AbstractPlayers.all_bid
		True
		"""

		return all(player.has_bid for player in cls)

	@property
	def repr_list(cls, /) -> list[str]:
		"""Return the string representation of all `Players` objects."""
		return [repr(player) for player in cls]

	def __call__(cls: type[P], playerindex: Optional[PlayerIndex] = None, /) -> P:
		# noinspection PyUnresolvedReferences
		"""Return an existing player if a player with that player_index already exists, else create a new `Player`.
		A design very similar to `enum.Enum` in the standard library.

		Parameters
		----------
		playerindex: `int` in range 0 <= x <= 5, or `None` (optional)
			When this parameter is `None` (the default): create a new instance of the class.

			When this parameter is an `int` in the range `0 <= x <=5`:
			retrieve an existing `Players` instance with that player_index.

		Returns
		-------
		A `Player` object.

		Raises
		------
		`InvalidPlayerindexException` if you enter a player_index for which there is no corresponding player.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=3)
		>>> p0 = AbstractPlayer()
		>>> type(p0) is AbstractPlayer
		True
		>>> p0 is AbstractPlayer(0)
		True
		>>> AbstractPlayer(2)
		Traceback (most recent call last):
		InvalidPlayerindexException: No player exists with that player_index.
		"""

		if playerindex is not None:
			try:
				player = cls._all_players_list[playerindex]
			except IndexError:
				raise InvalidPlayerindexException('No player exists with that player_index.')
			else:
				return player

		new = object.__new__(cls)
		new_player = cast(P, new)
		cls._all_players_list.append(new_player)
		new_player.__init__()
		return new_player

	def __getitem__(cls: type[P], playername: str, /) -> P:
		"""Return a `Player` object with a certain name associated with it.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p = AbstractPlayer()
		>>> p.name = 'Alex'
		>>> AbstractPlayers['Alex'] is p
		True
		"""

		return cls._all_players_dict[playername]

	def __iter__(cls: type[P], /) -> Iterator[P]:
		"""Iterate through the list of players.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=3)
		>>> len(AbstractPlayers.make_players()) == 3
		True
		>>> for player in AbstractPlayers:
		...     print(player.player_index)
		...
		0
		1
		2
		"""

		return iter(cls._all_players_list)

	def __len__(cls, /) -> PossibleLengthOfPlayersList:
		"""Return the number of players currently in the game.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> len(AbstractPlayers.make_players()) == len(AbstractPlayers) == 2
		True
		"""
		length = len(cls._all_players_list)
		return cast(PossibleLengthOfPlayersList, length)


C = TypeVar('C', bound=AbstractCard)


# We can't make this class generic due to the fact that we define __getitem__ in the metaclass...
# noinspection PyNestedDecorators
class AbstractPlayer(DataclassyReprBase, metaclass=PlayersMeta):
	"""Object representing a single player in the game."""

	__slots__ = '_bid', '_name', '_hand', '_hand_proxy'

	NON_REPR_SLOTS = frozenset({'_bid', '_name', '_hand', '_hand_proxy'})
	EXTRA_REPR_ATTRS = ('bid', 'name', 'hand', 'player_index')

	_hand: list[C]
	_hand_proxy: SequenceProxy[C]
	_name: Union[str, Placeholders]
	_bid: Union[Bid, Placeholders]

	MAX_NAME_LENGTH: Final = 30
	MIN_NAME_LENGTH: Final = 1

	def __init__(self, /) -> None:
		hand = []
		self._hand: Final = hand
		self._hand_proxy: Final = SequenceProxy(hand)
		self._name = Placeholders.NOT_YET_NAMED

		self._bid = Placeholders.NOT_YET_BID

	@property
	def player_index(self, /) -> PlayerIndex:
		# noinspection PyUnresolvedReferences
		"""Get the index of the player in the list of all players, an integer between 0 and 5 inclusive.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p0, p1 = AbstractPlayer(), AbstractPlayer()
		>>> p0.player_index, p1.player_index
		(0, 1)
		>>> AbstractPlayers.end_of_game()
		>>> p0.player_index, p1.player_index
		(1, 0)
		>>> p0.player_index = 5
		Traceback (most recent call last):
		AttributeError: can't set attribute
		"""

		return type(self).all_players_sequence.index(self)

	@property
	def hand(self, /) -> SequenceProxy[C]:
		# noinspection PyUnresolvedReferences
		"""Get a read-only "view" of the player's hand of cards.
		To modify the player's hand, methods `receive_cards` and `plays_card` must be used.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p = AbstractPlayer()
		>>> p.hand = []
		Traceback (most recent call last):
		AttributeError: can't set attribute
		>>> p.hand.append('Some card idk')
		Traceback (most recent call last):
		AttributeError: 'SequenceProxy' object has no attribute 'append'
		>>> p.hand
		SequenceProxy([])
		>>> print(p.hand)
		[]
		"""

		return self._hand_proxy

	@property
	def name(self, /) -> str:
		# noinspection PyUnresolvedReferences
		"""Get the name of the player.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p = AbstractPlayer()
		>>> print(p.name)
		<NOT_YET_NAMED>
		>>> p.name = 'Alex'
		>>> p.name
		'Alex'
		"""

		return self._name

	@name.setter
	def name(self, name: str, /) -> None:
		# noinspection PyUnresolvedReferences,PyProtectedMember
		"""Set the name of the player to a certain string after checking the value of the string.

		Additionally, add that information to the player's `hand` object,
		and add the player to the dictionary mapping players' player_names to `Players` objects.

		Prior to setting the name, the string is checked that it meets length requirements,
		and it is checked that no other player with that name already exists.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p = AbstractPlayer()
		>>> print(p.name)
		None
		>>> AbstractPlayers.all_players_mapping
		mappingproxy({})
		>>> p.name = 'Alex'
		>>> p.name == 'Alex'
		True
		>>> AbstractPlayers.all_players_mapping['Alex'] is AbstractPlayers.all_players_sequence[0] is p
		True
		>>> p2 = AbstractPlayer()
		>>> p2.name = 'Alex'
		Traceback (most recent call last):
		InvalidNameException: A player with the name 'Alex' already exists; please choose a different name.
		"""

		name_len = len(name)
		min_len, max_len = self.MIN_NAME_LENGTH, self.MAX_NAME_LENGTH
		cls = type(self)

		if name_len < min_len:
			raise InvalidNameException(f"A player's name must be a minimum of {min_len} characters long.")
		if name_len > max_len:
			raise InvalidNameException(f"A player's name cannot be any longer than {max_len} characters.")
		if name in cls.names:
			raise InvalidNameException(
				f"A player with the name '{name}' already exists; please choose a different name."
			)

		self._name = name
		cls.add_player_to_dict(player=self, name=name)

	@property
	def bid(self, /) -> Bid:
		# noinspection PyUnresolvedReferences
		"""Get the player's bid this round, an integer between 0 and 13 inclusive.

		Examples
		--------
		>>> p = AbstractPlayer()
		>>> p.bid
		<Placeholders.NOT_YET_BID>
		>>> print(p.bid)
		<NOT_YET_BID>
		>>> p.has_bid
		False
		>>> p.bid = 5
		>>> print(p.bid)
		5
		>>> p.has_bid
		True
		>>> del p.bid
		>>> p.bid
		<Placeholders.NOT_YET_BID>
		>>> p.bids(20)
		Traceback (most recent call last):
		ValueError: 20 is not a valid Bid
		>>> p.bids(2)
		>>> print(p.bid)
		2
		"""

		return self._bid

	@bid.setter
	def bid(self, bid: ValidBid, /) -> None:
		"""Set the player's bid at the beginning of a round.
		A player's bid can be an integer in the range `0 <= x <= 13`.
		See the "getter" method of the property for unit tests.
		"""

		self._bid = Bid(bid)

	@bid.deleter
	def bid(self, /) -> None:
		"""Reset the player's bid in preparation for the next round.
		See the "getter" method of the property for unit tests.
		"""

		# noinspection PyTypeChecker
		self._bid = Placeholders.NOT_YET_BID

	def bids(self, bid: ValidBid, /) -> None:
		"""Set the player's bid at the beginning of a round.
		A player's bid can be an integer in the range `0 <= x <= 13`.
		(This method is an alias for the "setter" method of the `bid` property, where examples/tests can be found.)
		"""

		self.bid = bid

	def reset_bid(self, /) -> None:
		"""Reset the player's bid in preparation for the next round.
		(This method is an alias for the deleter method of the `bid` property, where examples/tests can be found.)
		"""

		del self.bid

	@property
	def has_bid(self, /) -> bool:
		"""A boolean value: `True` if the player has bid this round, else `False`.
		See the `bid` property for examples/tests.
		"""

		# We can't just do `bool(self.bid)`, as `0` is a valid bid.
		return self._bid is not Placeholders.NOT_YET_BID

	@property
	def has_been_named(self, /) -> bool:
		# noinspection PyUnresolvedReferences
		"""A boolean value: `True` if the player's name has been set, else `False`.

		Examples
		--------
		>>> AbstractPlayers.reset_for_unit_test(player_number=2)
		>>> p = AbstractPlayer()
		>>> p.has_been_named
		False
		>>> p.name = 'Alex'
		>>> p.has_been_named
		True
		"""

		return isinstance(self._name, str)

	def receives_cards(self: P, cards: Sequence[C], /, *, trumpsuit: Suit) -> P:
		"""Receive a new hand of cards at the start of a round. Sort the cards upon receiving them.

		Parameters
		----------
		cards: A list of `Card` objects (see the `cards` module).
			The new hand of cards the player is receiving.

		trumpsuit: Suit (see the `Suit` module).
			This argument is relevant to the way the hand is sorted (the trump is usually on the left of the hand).

		Returns
		-------
		self
		"""

		self._hand.extend(cards)
		return self

	def __str__(self, /) -> str:
		return f'<Player {self.player_index}: {self.name}>'


# Alias for nicer iteration
AbstractPlayers = AbstractPlayer


if __name__ == '__main__':
	from doctest import testmod
	testmod()
