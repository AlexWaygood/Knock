"""Classes representing the simulation of a trick, round, game and tournament on the server side.
These classes are concrete implementations of the abstractions found in `abstract_game.py`.
"""

from __future__ import annotations

from typing import Sequence, Optional

from src.new_game.abstract_game import AbstractTournament, AbstractGame, AbstractRound, AbstractTrick
from src.players.players_server import ServerPlayer as Player, ServerPlayers as Players
from src.cards.server_card import ServerCard as Card, ServerPack as Pack


class ServerTrick(AbstractTrick[Card]):
	"""Object holding data and methods relevant to playing a trick on the server side."""
	cards = Pack

	def execute_play(self, /, *, card_id: str, player_index: int) -> None:
		"""Remove a card from a player's hand and append it to the `cards_on_board` list."""

		card = self._add_card_to_board(card_id=card_id)
		Player(player_index).hand.remove(card)


class ServerRound(AbstractRound[ServerTrick, Card]):
	"""Object holding data and methods relevant to playing a round on the server side."""

	def new_trick(self, /) -> ServerTrick:
		"""Start a trick in this round."""
		self.trick = trick = ServerTrick(parent=self)
		return trick


class ServerGame(AbstractGame[ServerRound, Card]):
	"""Object holding data and methods relevant to playing a game on the server side."""

	def new_round(self, /) -> ServerRound:
		"""Start a new round in this game."""

		self.round = game_round = ServerRound(parent=self, trump_card=self.next_round_trump_card())
		return game_round


class _ServerTournament(AbstractTournament[ServerGame, Player, Card]):
	"""Object holding data and methods relevant to playing a tournament on the server side.
	By itself, this class knows NOTHING about how to send update-messages to the client.
	It must be combined with the `_SendableToClientMixin` mixin (see below) in order to be useable.
	"""

	players = Players

	def new_game(self, /) -> ServerGame:
		"""Start a new game in this tournament."""

		self.game = game = ServerGame(start_card_number=self.next_game_start_number(), parent=self)
		return game


class _UpdateableFromClientsMixin:
	"""Mixin class containing methods relevant to updating the server simulation of the game from client messages."""


class _SendableToClientMixin:
	"""Mixin class containing methods relevant to serialising a tournament and packing it into messages to clients.
	This class is purely an implementation detail of the ServerTournament class.
	It has only one public method: `send_updates_to_client`.
	All other methods in this class are implementation details of that method.
	"""

	__slots__ = ()

	cards_on_board: list[Card]
	rematch_desired: bool
	game_in_progress: bool
	game: Optional[ServerGame]

	def send_updates_to_client(self, /) -> None:
		"""Serialise the state of the tournament into a string, queue a message to all clients with the string."""

		serialised_tournament = self._serialised()
		player: Player

		for player in Players:
			if serialised_tournament != 'WAIT':
				serialised_hand = self._serialised_hand_of_player(player)
				serialised_tournament += f'---{serialised_hand}'

			player.schedule_message_to_client(serialised_tournament)

	def _serialised(self, /) -> str:
		"""Serialise everything about the tournament, *except* for the client's current hand.
		(The client's hand is different for each client.)

		Called by `self.send_updates_to_client()`
		"""

		# If not all players have been named, then that's all the clients need to know.
		if not Players.all_players_named:
			return 'WAIT'

		player_names_and_bids = self._serialised_player_names_and_bids()
		cards_on_board = self._serialised_cards_on_board()
		rematch_desired = self._serialised_rematch_desired()
		game_info = self._serialised_game_info()
		return '---'.join((player_names_and_bids, cards_on_board, rematch_desired, game_info))

	def _serialised_player_names_and_bids(self, /) -> str:
		"""Return a string representing the names and bids of all players in the game.
		Called by `self._serialised()`
		"""

		return '--'.join(map(self._serialised_name_and_bid_of_player, Players))

	@staticmethod
	def _serialised_name_and_bid_of_player(player) -> str:
		"""Get the serialised name and bid of a player, suitable for sending over the network to the client.
		Called by `self._serialised_player_names_and_bids()`.
		"""

		if not Players.all_players_named:
			return player.name if player.has_been_named else '*'

		serialised_bid = player.bid if player.has_bid else '*'
		return f'{player.name}-{serialised_bid}'

	def _serialised_cards_on_board(self, /) -> str:
		"""Return a string representing the current cards on the board.
		Called by `self._serialised()`
		"""

		return self._cards_to_string(self.cards_on_board)

	def _serialised_rematch_desired(self, /) -> str:
		"""Return a string representing whether a rematch will be played."""
		return str(int(self.rematch_desired))

	def _serialised_game_info(self, /) -> str:
		"""Return the trumpcard if a round is underway, or the starting card number if a game is underway, or "0".
		Called by self._serialised()
		"""

		if game := self.game:
			if game_round := game.round:
				return self._serialised_trump_card(game_round.trump_card)
			return self._serialised_start_number(game)
		return '0'

	@staticmethod
	def _serialised_trump_card(trump_card: Card, /) -> str:
		"""Return a string representing the current trump card.
		Called by `self._serialised_game_info()`.
		"""

		return str(trump_card.index_in_pack)

	@staticmethod
	def _serialised_start_number(game: ServerGame, /) -> str:
		"""Return a string representing the start-card-number of the game.
		Called by `self._serialised_game_info()`
		"""

		return str(game.start_card_number)

	def _serialised_hand_of_player(self, player: Player) -> str:
		"""Return a string representing a specific player's current hand of cards.
		Called by `self.send_updates_to_client()`.
		"""

		return self._cards_to_string(player.hand)

	@staticmethod
	def _cards_to_string(cards_sequence: Sequence[Card]) -> str:
		"""Convert a sequence of cards to a string.
		Called by `self._serialised_cards_on_board` and `self._serialised_hand_of_player`.
		"""

		if not cards_sequence:
			return 'None'
		return '-'.join([str(card.index_in_pack) for card in cards_sequence])


class ServerTournament(_ServerTournament, _SendableToClientMixin):
	"""Object holding data and methods relevant to playing a tournament on the server side."""
