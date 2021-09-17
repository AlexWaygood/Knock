"""Classes representing the simulation of a trick, round, game and tournament on the client side.
These classes are concrete implementations of the abstractions found in `abstract_game.py`.
"""

from __future__ import annotations

from operator import methodcaller
from typing import TYPE_CHECKING, Optional, NamedTuple, Literal, Final, Iterator
from itertools import chain, cycle

from src.new_game.abstract_game import AbstractTournament, AbstractGame, AbstractRound, AbstractTrick
from src.players.players_client import ClientPlayer as Player, ClientPlayers as Players
from src.cards.client_card import ClientCard as Card, ClientPack as Pack
from src.new_game.client_scoreboard_data import Scoreboard
import src.config as rc

from pygame.time import delay

if TYPE_CHECKING:
	from src.cards import Suit
	from src.display.input_context import GameInputContextManager


PossibleTrickNumbers = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


class ClientTrick(AbstractTrick[Card]):
	"""Object holding data and methods relevant to playing a trick on the client side."""

	__slots__ = 'winner', 'whose_turn_player_index', 'player_order', 'trump_suit'

	cards = Pack
	players = Players

	def __init__(self, /, *, parent: ClientRound, trump_suit: Suit, first_player_index: int) -> None:
		super().__init__(parent=parent)
		self.winner = None
		self.whose_turn_player_index = None
		self.trump_suit: Final = trump_suit
		self.player_order = chain(range(first_player_index, len(self.players)), range(first_player_index))

	def play_trick(self, /, *, context: GameInputContextManager, pos: int) -> None:
		"""Game sequence for playing a trick."""

		with context(game_updates_needed=True):
			for i in range(len(self.players)):
				self.whose_turn_player_index = next(self.player_order)
				context.trick_click_needed = (len(self.cards_on_board) == pos)

				while len(self.cards_on_board) == i:
					delay(100)

	def execute_play(self, /, *, card_id: str, player_index: int) -> None:
		"""Transfer a card from the client's hand to the board, and queue a message to inform the server."""

		card = self._add_card_to_board(card_id=card_id)
		self.players(player_index).plays_card(card, trumpsuit=self.trump_suit)
		rc.client.queue_message(f'@C{card_id}{player_index}')

	def cleanup_after_completion(self, /) -> None:
		"""Determine the winner of the trick; delete references to this instance from the parent."""

		winning_card = max(
			self.cards_on_board,
			key=methodcaller('get_win_value', self.cards_on_board[0].suit, self.trump_suit)
		)

		winner = winning_card.owner
		winner.tricks_this_round += 1
		self.winner = winner

		for card in self.cards_on_board:
			card.owner = None

		super().cleanup_after_completion()


class ClientRound(AbstractRound[ClientTrick, Card, Player]):
	"""Object holding data and methods relevant to playing a round on the client side."""

	__slots__ = 'trick_number', 'trick_winner', 'round_leader', 'trump_suit'
	players = Players

	def __init__(self, /, *, parent: ClientGame, trump_card: Card, round_leader: Player) -> None:
		super().__init__(parent=parent, trump_card=trump_card)
		# These attributes are never altered.
		self.trump_suit: Final[Suit] = trump_card.suit
		self.round_leader: Final = round_leader

		# These attributes are altered in self.end_of_trick()
		self.trick_winner: Optional[Player] = None
		self.trick_number: PossibleTrickNumbers = 1

	def new_trick(self, /) -> ClientTrick:
		"""Start a trick in this round."""

		self.trick = trick = ClientTrick(
			parent=self,
			trump_suit=self.trump_suit,
			first_player_index=(self.trick_winner or self.round_leader).player_index
		)

		return trick

	def end_of_trick(self, /) -> None:
		"""Increment the trick number by 1, record the trick winner, delete the parent's reference to this instance."""

		self.trick_winner = self.trick.winner
		super().end_of_trick()
		self.trick_number += 1


class ClientGame(AbstractGame[ClientRound, Player, Card]):
	"""Object holding data and methods relevant to playing a game on the client side."""

	__slots__ = 'scoreboard', 'player_cycle', 'round_leader', 'round_number', 'card_number_this_round'

	NON_REPR_SLOTS = frozenset({'scoreboard', 'player_cycle'})
	players = Players

	def __init__(self, /, *, start_card_number: int, parent: _ClientTournament) -> None:
		super().__init__(start_card_number=start_card_number, parent=parent)

		# These attributes are never altered.
		self.scoreboard: Final = Scoreboard(start_card_number=start_card_number)
		self.player_cycle: Final[Iterator[Players]] = cycle(Players)

		# These attributes are altered in self.end_of_round()
		self.round_leader = next(self.player_cycle)
		self.round_number = 1
		self.card_number_this_round = start_card_number

	def new_round(self, /) -> ClientRound:
		"""Start a new round in this game."""

		trump_card = self.next_round_trump()

		round_of_game = ClientRound(
			parent=self,
			trump_card=trump_card,
			round_leader=self.round_leader
		)

		self.round = round_of_game
		return round_of_game

	def end_of_round(self, /) -> None:
		"""Perform cleanup at the end of the round, and update the scoreboard."""

		self.round_number += 1
		self.card_number_this_round -= 1
		self.round_leader = next(self.player_cycle)

		for player in Players:
			player.end_of_round()

		self.scoreboard.update_scores(round_number=self.round_number, card_number=self.card_number_this_round)
		super().end_of_round()


class _ClientTournament(AbstractTournament[ClientGame, Player, Card]):
	"""Object holding data and methods relevant to playing a tournament on the client side.
	By itself, this class knows NOTHING about how to update itself following a message from the server.
	It must be combined with the `_UpdateableFromServerMixin` mixin (see below).
	"""

	__slots__ = 'games_played',

	players = Players

	def __init__(self, /) -> None:
		super().__init__()
		# This attribute is altered in self.end_of_game()
		self.games_played = 0

	def new_game(self, /) -> ClientGame:
		"""Begin a new game, and send a message to the server to let them know."""
		self.rematch_desired = False

		# One player decides the starting card number.
		# That player updates it locally -- the local update adds the start-card-number to the deque.
		# After the local update, it's sent to the server.
		# The server, on receiving the message, appends the number to *its* deque.
		# It then sends the number on to all the clients, who also append it to *their* deques.
		# So, on both the server and client sides, the starting card number is obtained *within this class*
		# by popping left off the deque.

		start_card_number = self.next_game_start_number()
		game = ClientGame(start_card_number=start_card_number, parent=self)
		self.game = game
		rc.client.queue_message('@s')
		return game

	def end_of_game(self, /) -> None:
		"""End a game in this tournament."""

		super().end_of_game()
		self.games_played += 1


class UnpackedServerMessage(NamedTuple):
	"""The structure of an update-message from the server, after it's been split into pieces.

	Attributes
	----------
	`players_info`: `str`
		A string describing the names and bids of all players.

	`cards_on_board`: `str`
		A string describing all cards currently on the board. If the string is "0",
		the board is empty.

	`rematch_desired`: `bool`
		Only relevant at the end of the game.
		`True` if a client has signalled that a rematch is desired, else `False`.

	`game_info`: `str`
		This could be:
			- `None`, if a game is not in progress.
			- The starting card number, if a game is in progress, but a round is not.
			- The trumpcard, if a round is in progress.

	`player_hand`:
		A string describing all the cards in this player's hand,
		or `None` if the player currently holds no cards.
		The string may be
	"""

	players_info: str
	cards_on_board: str
	rematch_desired: bool
	game_info: Optional[str]
	player_hand: Optional[str]

	# noinspection PyTypeChecker,PyArgumentList
	@classmethod
	def from_server_msg(cls, server_update_msg: str):
		"""Instantiate this class directly from server-update messages."""

		split_msg = list(filter(bool, server_update_msg.split('---')))
		split_msg[2] = bool(split_msg[2])

		# The number of message components will be either 4 of 5.
		# If a game is not in progress, `game_info` will just be "0".

		if split_msg[3] == '0':
			split_msg[3] = None

		if len(split_msg) == 4:
			split_msg.append(None)

		return cls(*split_msg)


class _UpdateableFromServerMixin:
	"""Mixin class containing methods relevant to unpacking and deciphering messages received from the server.
	This class is purely an implementation detail of the ClientTournament class.
	It has only one public method: `update_from_server`.
	All other methods in this class are implementation details of that method.
	"""

	__slots__ = ()

	cards_on_board: list[Card]
	game: Optional[ClientGame]
	rematch_desired: bool
	game_in_progress: bool
	start_card_number: PossibleTrickNumbers

	def update_from_server(self, /, *, server_update_msg: str, player: Player) -> None:
		"""Update internal state following a message from the server."""

		# for key, value in zip(self.triggers.Server.keys(), string_list[0].split('--')):
		# 	self.triggers.Server[key] = int(value)

		if server_update_msg == 'WAIT':
			return

		unpacked_msg = UnpackedServerMessage.from_server_msg(server_update_msg)
		players_info, cards_on_board, tournament_stage_info, trump_card_info, player_hand_info = unpacked_msg

		self._update_player_names_from_server(players_info)
		self._update_cards_on_board_from_server(cards_on_board)
		self._update_tournament_stage_from_server(tournament_stage_info)

		if trump_card_info is not None and self.game is not None:
			self._update_trump_card_from_server(trump_card_info_str=trump_card_info)

		if player_hand_info is not None and not player.hand:
			self._update_player_hand_from_server(player_hand_info_str=player_hand_info)

	def _update_players_from_server(self, players_info_str: str) -> None:
		"""Called by self.update_from_server()."""

		if not Players.all_players_named:
			self._update_player_names_from_server(players_info_str)
		else:
			self._update_player_bids_from_server(players_info_str)

	@staticmethod
	def _update_player_names_from_server(player_info_str: str) -> None:
		"""Called by self._update_players_from_server()."""

		for player, name in zip(Players, player_info_str.split('--')):
			if name != '*':
				player.name = name

	@staticmethod
	def _update_player_bids_from_server(players_info_str: str) -> None:
		"""Called by self._update_players_from_server()."""

		for player_info in players_info_str.split('--'):
			name, bid = player_info.split('-')
			if bid != '*':
				Players[name].bid = int(bid)

	def _update_cards_on_board_from_server(self, cards_on_board_info_str: str) -> None:
		"""Called by self.update_from_server."""

		cards_on_board = self._cards_from_string(cards_on_board_info_str)
		for card in cards_on_board:
			if card not in self.cards_on_board:
				self.cards_on_board.append(card)
				# self.new_card_queues.PlayedCards.put(1)

	# noinspection PyTupleAssignmentBalance,PyDunderSlots,PyUnresolvedReferences
	def _update_tournament_stage_from_server(self, tournament_stage_info_str: str) -> None:
		"""Update three parts of internal state from a server-update message:
			- Whether the clients have signified at the end of the game that they would like a rematch.
			- Whether there is a game in progress at the moment.
			- The starting card number of the game currently in progress, if there is one in progress.
		"""

		info_components = tournament_stage_info_str.split('--')
		if len(info_components) == 2:
			rematch_desired_str, game_in_progress_str, next_start_card_number_str = *info_components, None
		else:
			rematch_desired_str, game_in_progress_str, next_start_card_number_str = info_components

		self.rematch_desired = bool(int(rematch_desired_str))
		self.game_in_progress = bool(int(game_in_progress_str))
		self.game_start_card_number = int(next_start_card_number_str)

	def _update_trump_card_from_server(self, /, *, trump_card_info_str: str) -> None:
		"""Update the trump card for the next round from a server-update message, if a game is in progress."""

		index_in_pack = int(trump_card_info_str)
		trump_card = Pack.card_with_pack_index(index_in_pack)
		self.game.next_round_trump_card_queue.append(trump_card)
		# self.new_card_queues.TrumpCard.put(1)

	def _update_player_hand_from_server(self, /, *, player_hand_info_str: str) -> None:
		...
		# self.new_card_queues.Hand.put(1)

	@staticmethod
	def _cards_from_string(cards_string: str) -> list[Card]:
		"""Convert a string sent to us by the server into a list of cards.
		Called by `self._update_player_hand_from_server` and `self.update_cards_on_board_from_server()`.
		"""

		return [Pack.card_with_pack_index(int(i)) for i in cards_string.split('-')]


class ClientTournament(_ClientTournament, _UpdateableFromServerMixin):
	"""Object holding data and methods relevant to playing a tournament on the client side."""
