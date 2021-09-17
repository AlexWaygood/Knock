"""A class representing a player in the game.

The `ServerPlayers` class in this module is an extension of the `Players` class in `players_abstract.py`,
with some added logic that is specific to server-side mechanics.

Also included in this module is a metaclass to support the `ServerPlayers` class.
"""

from __future__ import annotations

from typing import ClassVar, TypeVar, TYPE_CHECKING
from operator import attrgetter
from collections import deque

from src.players.players_abstract import PlayersMeta, AbstractPlayer
# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import delay

if TYPE_CHECKING:
	from src import ConnectionAddress

	# noinspection PyTypeChecker
	S = TypeVar('S', bound='ServerPlayers')

action_complete = attrgetter('action_complete')


class ServerPlayersMeta(PlayersMeta):
	"""An extension of the `PlayersMeta` class in `players_abstract.py`.

	All methods in this metaclass *could* be implemented as `classmethod`s in the `ServerPlayers` class,
	but have been implemented in an extension of the metaclass for consistency's sake.
	(In the abstract `Players` class, all methods operating on the class are separated into the metaclass.)
	"""

	_all_players_list: ClassVar[list[ServerPlayer]]
	_all_players_dict: ClassVar[dict[str, ServerPlayer]]

	def next_stage(cls, /) -> None:
		"""Begin the next stage of the game."""

		for player in cls:
			player.action_complete = False

	def wait_for_players(cls, /) -> None:
		"""Sleep until all the players have finished this stage of the game."""

		while any(not action_complete(player) for player in cls):
			delay(1)

		cls.next_stage()


class ServerPlayer(AbstractPlayer, metaclass=ServerPlayersMeta):
	"""Object representing a single player on the serverside.

	This class represents the abstract concept of a player,
	and also has some serverside logic relating to communicating over the network with a client.
	"""

	__slots__ = '_game_update_message_queue', '_addr', 'action_complete'

	NON_REPR_SLOTS: ClassVar = frozenset({'_game_update_message_queue', '_addr'})
	EXTRA_REPR_ATTRS: ClassVar = 'action_complete', 'addr'

	_addr: ConnectionAddress
	action_complete: bool
	_game_update_message_queue: deque[str]

	def __init__(self, /) -> None:
		super().__init__()
		self.action_complete = False
		self._game_update_message_queue = deque(maxlen=1)

	@property
	def addr(self, /) -> ConnectionAddress:
		"""Get the connection address of the client associated with this instance."""
		return self._addr

	def connect(self: S, /, addr: ConnectionAddress, game_info: str) -> S:
		"""Connect to the client, add their connection address to self."""

		self._addr = addr
		self.schedule_message_to_client(game_info)
		return self

	@AbstractPlayer.bid.setter
	def bid(self: S, number: int, /) -> S:
		"""Set the player's bid."""

		# noinspection PyArgumentList
		AbstractPlayer.bid.fset(self, number)
		self.action_complete = True
		return self

	def schedule_message_to_client(self, game_string: str, /) -> None:
		"""Add a new update to the message queue, and discard the older one if there's an older one in the deque.
		(We're only interested in sending the client the most recent update.)
		"""

		self._game_update_message_queue.append(game_string)

	@property
	def next_message_to_client(self, /) -> str:
		"""Get the next message to the client, if one has been scheduled, else the default ping-pong message."""

		if self._game_update_message_queue:
			return self._game_update_message_queue.popleft()
		return 'pong'


ServerPlayers = ServerPlayer
