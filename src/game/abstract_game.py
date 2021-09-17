"""Class representing a game of Knock in the abstract
A base class for both the serverside and clientside simulations to inherit from).
"""

from __future__ import annotations

from typing import Generic, TypeVar, Union, NamedTuple, Iterable, Literal, cast, Iterator
from abc import abstractmethod
from src import DocumentedPlaceholderEnum, DataclassyReprBase, config as rc
from src.players.players_abstract import AbstractPlayer as Player, AbstractPlayers as Players
from src.cards import Suit
from src.cards.abstract_card import AbstractCard
from itertools import cycle


C = TypeVar('C', bound=AbstractCard)
P = TypeVar('P', bound=Player)


class Placeholders(DocumentedPlaceholderEnum):
	"""Placeholder singletons for the `game` module."""

	# Placeholders used in this module
	START_NUMBER_NOT_KNOWN = 'Placeholder value signifying it is not yet known how many cards the game will start with.'
	TRUMP_CARD_NOT_KNOWN = 'Placeholder value signifying the trump card is not yet known.'
	TRUMP_SUIT_NOT_KNOWN = 'Placeholder value signifying the trump suit is not yet known.'
	PARAMETERS_NOT_KNOWN = 'Placeholder value signifying the game parameters are not yet known.'

	# Clientside-specific placeholders
	ROUND_LEADER_NOT_KNOWN = 'Placeholder value signifying the round leader is not yet known.'
	WHOSE_TURN_NOT_KNOWN = 'Placeholder value signifying it is not yet known whose turn it is or will next be.'
	CARD_NUMBER_NOT_KNOWN = 'Placeholder value signifying it is not yet known how many cards there will be this round.'
	TRICK_NOT_IN_PROGRESS = 'Placeholder value for when a trick is not in progress'
	TRICK_WINNER_NOT_KNOWN = 'Placeholder value for when the trick winner is not yet known.'


StartCardNumberPossibilities = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
StartCardNumberType = Union[StartCardNumberPossibilities, Literal[Placeholders.START_NUMBER_NOT_KNOWN]]

TrumpCardType = Union[tuple[C], Literal[Placeholders.TRUMP_CARD_NOT_KNOWN]]
TrumpSuitType = Union[Suit, Literal[Placeholders.TRUMP_SUIT_NOT_KNOWN]]
GameParameterIterator = Iterator[tuple[int, int, Player]]


class GameParameters(NamedTuple):
	"""A tuple of iterators.

	One iterator representing the round number,
	one iterator representing the card number for each round,
	and one iterator representing the player leading each round.
	"""

	which_round: range[int]
	how_many_cards: range[int]
	who_leads: cycle[Player]

	@classmethod
	def from_start_card_number(cls, start_card_number: int, /, *, players: Iterable[Players]):
		"""Construct a `GameParameters` tuple from the starting card number and the list of players."""

		# noinspection PyArgumentList
		return cls(
			which_round=range(1, (start_card_number + 1)),
			how_many_cards=range(start_card_number, 0, -1),
			who_leads=cycle(players)
		)

	def __iter__(self) -> GameParameterIterator:
		which_round, how_many_cards, who_leads = iter(self.which_round), iter(self.how_many_cards), self.who_leads

		while True:
			yield next(which_round), next(how_many_cards), next(who_leads)


# noinspection PyPropertyDefinition
class AbstractGame(DataclassyReprBase, Generic[C, P]):
	"""Class representing a game of Knock in the abstract, to server as a base class for ServerGame and ClientGame.

	Attributes
	----------
	_play_started: `bool`
		`True` if the game has started in earnest, else `False`.
		(This will only be `False` when the game has yet to start, or the players are between games).

	repeat_game: `bool`
		???
	"""

	__slots__ = '_play_started', 'repeat_game', '_start_card_number', 'played_cards', '_trump_card', '_parameters'

	_play_started: bool
	repeat_game: bool
	played_cards: list[C]
	_trump_card: TrumpCardType[C]
	_start_card_number: StartCardNumberType
	_parameters: Union[GameParameterIterator, Literal[Placeholders.PARAMETERS_NOT_KNOWN]]

	def __init__(self, /) -> None:
		# The PlayerNumber is set as an instance variable on the server side but a class variable on the client side.
		# So we don't bother with it here.

		self.repeat_game = True
		self.played_cards = []
		self._play_started = False
		self._start_card_number = Placeholders.START_NUMBER_NOT_KNOWN
		self._trump_card = Placeholders.TRUMP_CARD_NOT_KNOWN
		self._parameters = Placeholders.PARAMETERS_NOT_KNOWN

	@property
	def play_started(self, /) -> bool:
		"""`True` if the game has started, else `False` if we have not yet started or are between games."""
		return self._play_started

	@property
	def trump_card(self, /) -> TrumpCardType:
		"""Get the trump card for this round."""
		return self._trump_card

	@trump_card.setter
	def trump_card(self, card: C, /) -> None:
		"""Set the trump card for this round."""
		self._trump_card = card

	@trump_card.deleter
	def trump_card(self, /) -> None:
		"""Reset the trump card to the placeholder default value, in preparation for the next round."""
		self._trump_card = Placeholders.TRUMP_CARD_NOT_KNOWN

	@property
	def trump_suit(self, /) -> TrumpSuitType:
		"""Get the trump suit for this round."""

		if self.trump_card is Placeholders.TRUMP_CARD_NOT_KNOWN:
			return Placeholders.TRUMP_SUIT_NOT_KNOWN
		return self.trump_card[0].suit

	@classmethod
	@property
	@abstractmethod
	def players(cls) -> type[P]:
		"""Return `ClientPlayers for the clientside simulation, and `ServerPlayers for the serverside."""
		return Players

	@classmethod
	@property
	@abstractmethod
	def cards(cls) -> type[C]:
		"""Return `ClientPack` for the clientside simulation, and `ServerPack` for the serverside."""

	@property
	def start_card_number(self, /) -> int:
		"""Get the number of cards the game is starting with."""
		return self._start_card_number

	@start_card_number.setter
	def start_card_number(self, number: Union[str, StartCardNumberPossibilities], /) -> None:
		"""Set the number of cards the game is starting with."""

		n = int(number)
		self._start_card_number = cast(StartCardNumberPossibilities, n)

	@start_card_number.deleter
	def start_card_number(self, /) -> None:
		self._start_card_number = Placeholders.START_NUMBER_NOT_KNOWN

	@property
	def parameters(self, /) -> GameParameters:
		"""Return a `NamedTuple` containing iterators for the round number, the card number, and the round leader."""
		params = GameParameters.from_start_card_number(self.start_card_number, players=self.players)
		self._parameters = iter(params)
		return params

	# noinspection PyPep8Naming
	def execute_play(self, cardID: str, playerindex: int) -> None:
		"""Remove the card from the player's hand and append it to the list of played cards for this trick."""

		card = self.cards(cardID)
		self.players(playerindex).plays_card(card, trumpsuit=self.trump_suit)
		self.played_cards.append(card)

	def end_round(self, /) -> None:
		"""Reset the trump card at the end of the round to the default placeholder."""
		del self.trump_card

	def new_game_reset(self, /) -> None:
		"""Reset internal state in preparation for a new game."""

		del self._start_card_number
		self.players.end_of_game()
		self._play_started = False

	@property
	@abstractmethod
	def _attrs_string(self, /) -> str:
		"""Helper for the __repr__ function; must be overriden in concrete subclasses."""

		return (
			f'start_play={self.play_started}, '
			f'repeat_game={self.repeat_game}, '
			f'player_number={rc.player_number}, '
			f'start_card_number={self._start_card_number}, '
			f'trump_card={self.trump_card!r}, '
			f'trumpsuit={self.trump_suit!r}, '
			f'played_cards={[repr(card) for card in self.played_cards]}, '
			f'players={self.players.repr_list}'
		)


def events_dict() -> dict[str, int]:
	return {
		'game_initialisation': 0,
		'RoundStart': 0,
		'new_pack': 0,
		'CardsDealt': 0,
		'TrickStart': 0,
		'TrickWinnerLogged': 0,
		'TrickEnd': 0,
		'RoundEnd': 0,
		'PointsAwarded': 0,
		'WinnersAnnounced': 0,
		'tournament_leaders_text': 0,
		'new_game_reset': 0,
		'StartNumberSet': 0
	}
