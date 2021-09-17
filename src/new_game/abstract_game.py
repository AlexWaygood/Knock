"""Abstract interfaces for both the client and server implementations to inherit from."""

from __future__ import annotations
from abc import abstractmethod, ABCMeta
from typing import Optional, Generic, final, TypeVar, TYPE_CHECKING, Final, Literal, Callable, ClassVar
from collections import deque
from src import DataclassyReprBase
import src.config as rc
from src.players.players_abstract import AbstractPlayers
from src.cards.abstract_card import AbstractCard

if TYPE_CHECKING:
	from src.special_knock_types import ExitArg1, ExitArg2, ExitArg3

PossibleStartNumbers = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
C = TypeVar('C', bound=AbstractCard)
P = TypeVar('P', bound=AbstractPlayers)

# noinspection PyTypeChecker
GC = TypeVar('GC', bound='GameStageContextManager')


class _KnowsCardsOnBoard(Generic[C]):
	"""GameStageContextManager and KnockTournament both inherit directly from this mixin class."""
	cards_on_board: Final[list[C]] = []


class GameStageContextManager(DataclassyReprBase, _KnowsCardsOnBoard[C], metaclass=ABCMeta):
	"""All stages in a Knock tournament (a game, a round, and a trick) inherit from this base class."""

	__slots__ = 'parent', 'players'

	@final
	def __enter__(self: GC, /) -> GC:
		"""Enter a `with` statement."""
		return self

	@abstractmethod
	def cleanup_after_completion(self, /) -> None:
		"""Perform cleanup actions required after exiting a `with` statement."""

	@final
	def __exit__(self, exc_type: ExitArg1, exc_val: ExitArg2, exc_tb: ExitArg3, /) -> None:
		"""Exit a `with` statement, performing some necessary cleanup but letting all exceptions persist."""
		self.cleanup_after_completion()


class AbstractTrick(GameStageContextManager[C]):
	"""A class representing a trick of this game in the abstract;
	a common interface used by the server script and client script.
	"""

	__slots__ = ()

	@property
	@abstractmethod
	def cards(self, /) -> type[C]:
		"""Define the class representing a pack of cards for a particular concrete subclass."""
		return AbstractCard

	def __init__(self, /, *, parent: AbstractRound) -> None:
		# None of this class's attributes are ever altered.
		self.parent: Final = parent

	def _add_card_to_board(self, /, *, card_id: str) -> C:
		card = self.cards(card_id)
		self.cards_on_board.append(card)
		return card

	@abstractmethod
	def execute_play(self, /, *, card_id: str, player_index: int) -> None:
		"""Remove a card from a player's hand and append it to the `cards_on_board` list."""

	def cleanup_after_completion(self, /) -> None:
		"""Clear the board and delete the references in the parent class to this instance."""
		self.cards_on_board.clear()
		self.parent.end_of_trick()


T = TypeVar('T', bound=AbstractTrick)


class AbstractRound(Generic[T, C], GameStageContextManager[C]):
	"""A class representing a round of this game in the abstract;
	a common interface used by the server script and client script.
	"""

	__slots__ = 'trump_card', 'trick'

	def __init__(self, /, *, parent: AbstractGame, trump_card: C) -> None:
		# These attributes are never altered
		self.parent: Final = parent
		self.trump_card: Final = trump_card

		# This attribute is altered in self.new_trick() and self.end_of_trick()
		self.trick: Optional[T] = None

	@property
	def trick_in_progress(self, /) -> bool:
		"""`True` if a trick is currently in progress, else `False`."""
		return self.trick is not None

	def cleanup_after_completion(self, /) -> None:
		"""Delete references in the parent class to this instance."""
		self.parent.end_of_round()

	@abstractmethod
	def new_trick(self, /) -> T:
		"""Start a trick in this round."""

	def end_of_trick(self, /) -> None:
		"""End a trick in this round."""
		self.trick = None


R = TypeVar('R', bound=AbstractRound)


class AbstractGame(Generic[R, C], GameStageContextManager[C]):
	"""A class representing a game of Knock in the abstract;
	a common interface used by the server script and client script.
	"""

	__slots__ = 'round', 'start_card_number', '_next_round_trump_card_queue', 'next_round_trump_card'

	NON_REPR_SLOTS = frozenset('player_cycle',)

	def __init__(self, /, *, start_card_number: int, parent: AbstractTournament) -> None:
		trump_card_queue = deque(maxlen=1)

		# This attribute is appended to in updates from the server and popped from in self.new_round()
		self._next_round_trump_card_queue: Final[deque[C]] = trump_card_queue

		# These attributes are never altered
		self.next_round_trump_card: Final[Callable[[], C]] = trump_card_queue.popleft
		self.start_card_number: Final = start_card_number
		self.parent: Final = parent

		# These attributes are altered in self.new_round() and self.end_of_round()
		self.round: Optional[R] = None

	@property
	def round_in_progress(self, /) -> bool:
		"""`True` if a round is currently in progress, else `False`."""
		return self.round is not None

	def cleanup_after_completion(self, /) -> None:
		"""Delete references in the parent class to this instance."""
		self.parent.end_of_game()

	@abstractmethod
	def new_round(self, /) -> R:
		"""Start a new round in this game."""

	def end_of_round(self, /) -> None:
		"""End a round in this game."""
		self.round = None


G = TypeVar('G', bound=AbstractGame)


class AbstractTournament(Generic[G, P, C], DataclassyReprBase, _KnowsCardsOnBoard[C]):
	"""A class representing a tournament of Knock in the abstract;
	a common interface used by the server script and client script.
	"""

	__slots__ = 'game', 'rematch_desired', '_next_game_start_number_queue', 'next_game_start_number'
	EXTRA_REPR_ATTRS: ClassVar = 'game_in_progress',

	@property
	@abstractmethod
	def players(self, /) -> type[P]:
		"""Get the class being used to represent a player.

		(This is an abstract property abstract, as this detail will vary depending
		on whether this is the clientside simulation or the serverside simulation).
		"""

		return AbstractPlayers

	def __init__(self, /) -> None:
		# Set up the players for the tournament
		self.players.make_players()

		# This is altered externally and in self.new_game()
		self.rematch_desired = False

		start_number_queue = deque(maxlen=1)

		# This attribute is appended to in updates from the server and popped from in self.new_game()
		self._next_game_start_number_queue: deque[PossibleStartNumbers] = start_number_queue

		# This attribute is never altered
		self.next_game_start_number: Final[Callable[[], PossibleStartNumbers]] = start_number_queue.popleft

		# This attributes are altered in self.new_game() and self.end_of_game()
		self.game: Optional[G] = None

	@property
	def player_has_departed(self, /) -> bool:
		"""`True` if a player has left the game, else `False`"""
		return self.game_in_progress and rc.player_number != len(self.players)

	@property
	def game_in_progress(self, /) -> bool:
		"""`True` if a game is in progress, else `False`."""
		return self.game is not None

	@abstractmethod
	def new_game(self, /) -> G:
		"""Start a new game in this tournament."""

	def end_of_game(self, /) -> None:
		"""End a game in this tournament."""

		self.game = None
		self.players.end_of_game()
