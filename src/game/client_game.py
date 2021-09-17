"""Class representing the clientside simulation of a game of Knock."""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Annotated, Literal, cast, Union, TypeVar
from itertools import chain
from queue import Queue
from operator import methodcaller

from src.game import AbstractGame, events_dict, Placeholders
from src.game.client_scoreboard_data import Scoreboard
from src.players.players_client import ClientPlayer as Player, ClientPlayers as Players
from src.cards.client_card import ClientCard as Card, ClientPack as Pack

# noinspection PyUnresolvedReferences
from src import pre_pygame_import, config as rc
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import ExitArg1, ExitArg2, ExitArg3
	from src.display import GameInputContextManager

PlayerIndicies = Literal[0, 1, 2, 3, 4, 5]
PlayerOrderList = Annotated[list[PlayerIndicies], "An integer list of indexes indicating the order of players"]
RoundNumberPossibilities = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

TrickNumberPossibilities = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
TrickNumberType = Union[Literal[Placeholders.TRICK_NOT_IN_PROGRESS], TrickNumberPossibilities]

CardNumberPossibilities = Union[RoundNumberPossibilities, Literal[Placeholders.CARD_NUMBER_NOT_KNOWN]]
MaxCardNumberPossibilities = Literal[8, 10, 12, 13]

RoundLeaderIndexPossibilities = Union[Literal[Placeholders.ROUND_LEADER_NOT_KNOWN], PlayerIndicies]
WhoseTurnPossibilities = Union[Literal[Placeholders.WHOSE_TURN_NOT_KNOWN], PlayerIndicies]

# noinspection PyTypeChecker
G = TypeVar('G', bound='ClientGame')


class NewCardQueues:
	__slots__ = 'Hand', 'PlayedCards', 'TrumpCard'

	def __init__(self) -> None:
		self.Hand = Queue()
		self.PlayedCards = Queue()
		self.TrumpCard = Queue()


class DoubleTrigger:
	__slots__ = 'Client', 'Server'

	def __init__(self, /) -> None:
		self.Client = events_dict()
		self.Server = events_dict()

	def __enter__(self, /) -> DoubleTrigger:
		return self

	def __exit__(self, exc_type: ExitArg1, exc_val: ExitArg2, exc_tb: ExitArg3) -> None:
		pass


# noinspection PyPropertyDefinition
class ClientGame(AbstractGame[Card, Player]):
	"""Class representing the clientside simulation of a game of Knock."""

	__slots__ = (
		'games_played', 'card_number_this_round', 'round_number', 'trick_in_progress', 'trick_number',
		'_whose_turn_player_index', 'player_order', 'round_leader_index', 'max_card_number', 'new_card_queues',
		'scoreboard', '_game_context', '_round_context', 'trick_winner'
	)

	triggers: DoubleTrigger
	scoreboard: Scoreboard
	new_card_queues: NewCardQueues
	player_order: PlayerOrderList
	games_played: int
	round_number: RoundNumberPossibilities
	max_card_number: MaxCardNumberPossibilities
	card_number_this_round: CardNumberPossibilities
	round_leader_index: RoundLeaderIndexPossibilities
	trick_number: TrickNumberType
	_whose_turn_player_index: WhoseTurnPossibilities
	trick_winner: Union[Players, Literal[Placeholders.TRICK_WINNER_NOT_KNOWN]]

	def __init__(self, /) -> None:
		super().__init__()

		self.triggers = DoubleTrigger()

		Players.make_players()

		self.scoreboard = Scoreboard()
		self.new_card_queues = NewCardQueues()
		self.player_order = []

		self.games_played = 0
		self.round_number = 1
		self.trick_in_progress = False

		max_card_number = min(13, (51 // rc.player_number))
		self.max_card_number = cast(MaxCardNumberPossibilities, max_card_number)

		self.card_number_this_round = Placeholders.CARD_NUMBER_NOT_KNOWN
		self.round_leader_index = Placeholders.ROUND_LEADER_NOT_KNOWN
		self.trick_number = Placeholders.TRICK_NOT_IN_PROGRESS
		self._whose_turn_player_index = Placeholders.WHOSE_TURN_NOT_KNOWN

		self._game_context = False
		self._round_context = False
		self.trick_winner = Placeholders.TRICK_WINNER_NOT_KNOWN

	@classmethod
	@property
	def players(cls) -> type[Players]:
		"""Get the `Players` class that this simulation of the game is using.
		This is the clientside simulation, so we return `ClientPlayers`.
		"""

		return Players

	@classmethod
	@property
	def cards(cls) -> type[Card]:
		"""Get the `Cards` class that this simulation of the game is using.
		This is the clientside simulation, so we return `ClientCard`.
		"""

		return Card

	@property
	def whose_turn_player_index(self, /) -> int:
		"""Get the player index of the person whose turn it is."""
		return self._whose_turn_player_index

	@whose_turn_player_index.deleter
	def whose_turn_player_index(self, /) -> None:
		"""Reset this attribute to the placeholder value."""
		self._whose_turn_player_index = Placeholders.WHOSE_TURN_NOT_KNOWN

	def time_to_start(self, /) -> None:
		"""Set `play_started` to True and send a message to the server."""

		self._play_started = True
		rc.client.queue_message('@s')

	@AbstractGame.start_card_number.setter
	def start_card_number(self, number: Union[RoundNumberPossibilities, str]) -> None:
		"""Set the number of cards the game will start with."""
		self._start_card_number = int(number)
		self.scoreboard.setup(self._start_card_number)

	def attribute_wait(self, attr: str) -> None:
		"""Wait until the server indicates that it is time for the next stage of the game to start."""

		with self.triggers as s:
			while s.Server[attr] == s.Client[attr]:
				delay(100)

			s.Client[attr] = s.Server[attr]

	def trick_context(
			self,
			trick_number: TrickNumberPossibilities,
			first_player_index: PlayerIndicies,
			player: Players
	) -> tuple[PlayerOrderList, int]:
		"""Set up the conditions necessary for a new trick to be played."""

		self.trick_in_progress = True
		self.trick_number = trick_number
		self.player_order = list(chain(range(first_player_index, rc.player_number), range(first_player_index)))
		player.pos_in_trick = self.player_order.index(player.player_index)
		return self.player_order, player.pos_in_trick

	def play_trick(self, context: GameInputContextManager, pos: int) -> None:
		"""Game sequence for playing a trick."""

		with context(GameUpdatesNeeded=True):
			for i, val in enumerate(self.player_order):
				self._whose_turn_player_index = val
				context.trick_click_needed = (len(self.played_cards) == pos)

				while len(self.played_cards) == i:
					delay(100)

	# noinspection PyPep8Naming
	def execute_play(self, cardID: str, playerindex: int) -> None:
		"""Remove the card from the player's hand, append it to the list of played cards this trick, tell the server."""

		super().execute_play(cardID, playerindex)
		rc.client.queue_message(f'@C{cardID}{playerindex}')

	def end_trick(self) -> None:
		"""Reset internal state following the end of a trick."""

		winning_card = max(self.played_cards, key=methodcaller('get_win_value', self.played_cards[0].Suit, self.trumpsuit))
		winner = Players[winning_card.PlayedBy]
		winner.tricks_this_round += 1

		if self.trick_number != self.card_number_this_round:
			del self.whose_turn_player_index
			self.trick_in_progress = False

		self.trick_winner = winner

	def end_round(self) -> None:
		"""Reset internal state following the end of a round."""

		del self.whose_turn_player_index
		self.trick_in_progress = False

		for player in Players:
			player.end_of_round()

		self.scoreboard.update_scores(self.round_number, self.card_number_this_round)
		super().end_round()

		if self.round_number != self.start_card_number:
			self.round_number += 1
			self.card_number_this_round -= 1
			self.trick_number = 1

	def new_game_reset(self) -> None:
		"""Reset internal state at the end of a game."""

		super().new_game_reset()
		Players.end_of_game()
		self.round_number = 1

	@property
	def player_has_departed(self, /) -> bool:
		"""Return `True` if a player has left the game, else `False`"""
		return self.play_started and rc.player_number != len(self.players)

	def gameplay_context(self, /):
		return self

	def round_context(self, /):
		"""Make the necessary changes to internal state for a round to begin.
		Intended for use as a context manager, e.g.:

		>>> g = ClientGame()
		>>>
		>>> with ClientGame().round_context():
		>>>
		"""
		self.card_number_this_round, self.round_leader_index, self.round_number = next(self._parameters)
		self._round_context = True
		return self

	def __enter__(self) -> ClientGame:
		return self

	def __exit__(self, exc_type: ExitArg1, exc_val: ExitArg2, exc_tb: ExitArg3) -> None:
		if self.trick_in_progress:
			self.end_trick()
			self.trick_in_progress = False
		elif self._round_context:
			self.end_round()
			self._round_context = False
		elif self._play_started:
			self.new_game_reset()

	@property
	def _attrs_string(self, /) -> str:
		"""Helper for the __repr__ function"""

		return super()._attrs_string + (
			f'games_played={self.games_played}, '
			f'card_number_this_round={self.card_number_this_round}, '
			f'round_number={self.round_number}, '
			f'trick_in_progress={self.trick_in_progress}, '
			f'trick_number={self.trick_number}, '
			f'_whose_turn_playerindex={self._whose_turn_player_index}, '
			f'player_order={self.player_order}, '
			f'round_leader_index={self.round_leader_index}, '
			f'max_card_number={self.max_card_number}'
		)

	# PlayerNumber is given in the abstract_game repr
	def __repr__(self) -> str:
		added = f'''


'''
		return '\n'.join((super().__repr__(), added))

	def update_from_server(self, string: str, playerindex: int) -> None:
		"""Update internal state following a message from the server."""

		string_list = string.split('---')

		for key, value in zip(self.triggers.Server.keys(), string_list[0].split('--')):
			self.triggers.Server[key] = int(value)

		player_info_list = string_list[1].split('--')

		if not Players.all_players_named:
			for player, playerinfo in zip(Players, player_info_list):
				player.name = attempt_to_int(playerinfo.split('-')[0])
		else:
			for info in player_info_list:
				name, bid = info.split('-')
				player = Players(name)

				if bid == '*1':
					del player.bid
				else:
					player.bid = int(bid)

		if (PlayedCards := string_list[2]) != 'None':
			self.played_cards = cards_from_string(PlayedCards)
			self.new_card_queues.PlayedCards.put(1)

		tournament_string = string_list[3]
		self._play_started, self.RepeatGame = [bool(int(tournament_string[i])) for i in range(2)]
		self.start_card_no = int(tournament_string[2])

		if not self.TrumpCard:
			with suppress(KeyError):
				self.TrumpCard = (Card(attempt_to_int(tournament_string[3]), tournament_string[4]),)
				self.trumpsuit = self.TrumpCard[0].Suit
				self.new_card_queues.TrumpCard.put(1)

		if (Hand := string_list[4]) != 'None' and not Players(playerindex).hand:
			Players(playerindex).hand.new_hand(cards_from_string(Hand))
			self.new_card_queues.Hand.put(1)


def attempt_to_int(string: str, /) -> Union[str, int]:
	"""Return an `int` if the string is `int`-able, else return the string unchanged."""

	try:
		return int(string)
	except ValueError:
		return string


def cards_from_string(cards_string: str) -> list[Card]:
	"""Convert a string sent to us by the server into a list of cards."""
	return [Pack.card_with_pack_index(int(i)) for i in cards_string.split('-')]
