"""A class representing a player in the game.

The `ClientPlayers` class in this module is an extension of the `Players` class in `players_abstract.py`,
with some added logic that is specific to client-side mechanics.

Also included in this module is a metaclass to support the `ClientPlayers` class, and a `ClientHand` class,
which is an extension of the `hand` class in `players_abstract.py`.
"""

from __future__ import annotations

from typing import Iterator, TypeVar, NamedTuple, Literal, cast, Iterable, Optional, ClassVar
from operator import attrgetter
from itertools import groupby, chain

import src.config as rc

from src import Position, IntEnumNiceStr
from src.static_constants import ScoreboardTextKeys, TextAlignment, BoardSurfFonts

from src.players.players_abstract import PlayersMeta, AbstractPlayer, ValidBid, Placeholders
from src.players import sort_hand_in_place

from src.cards import Suit
from src.cards.client_card import ClientCard as Card

StringIterator = Iterator[str]
PossibleTricksWinnings = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

# noinspection PyTypeChecker
H = TypeVar('H', bound='HandSnapshotTuple')

# Needs to be available at runtime for `typing.cast()`
PossiblePointsScored = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23]

# noinspection PyTypeChecker
P = TypeVar('P', bound='ClientPlayers')
get_points = attrgetter('points')


class TrickPosition(IntEnumNiceStr):
	"""An enumeration of all possible positions a player may have in a trick."""

	POSITION_NOT_YET_KNOWN = -1
	ZERO = 0
	ONE = 1
	TWO = 2
	THREE = 3
	FOUR = 4
	FIVE = 5


class BoardTextArgs(NamedTuple):
	"""`NamedTuple` containing the arguments needed for `Players.board_text()`.
	Many of these arguments are then passed on directly to `Players.board_text_helper()`.
	"""

	whose_turn: int
	trick_in_progress: bool
	played_cards_no: int
	linesize: int
	round_leader_index: int


class LineOfBoardText(NamedTuple):
	"""NamedTuple representing the arguments needed for constructing a single line of text on the board."""
	text: str
	font_name: str
	position: Position


class LineOfScoreboardText(NamedTuple):
	"""NamedTuple representing the arguments needed for constructing a single line of text on the scoreboard."""
	text: str
	position_kwargs: dict[str, Position]


class HandSnapshotTuple(NamedTuple):
	"""A `NamedTuple` representing a snapshot of a player's hand of cards immediately before playing a card.

	The specific information recorded is the suit of the first card in the player's hand,
	and the suit of the last card in the player's hand,
	at the moment before the playing of the card took place.
	"""

	first_card_suit: Suit
	last_card_suit: Suit

	@classmethod
	def of_hand(cls: type[H], hand: list[Card]) -> H:
		# noinspection PyUnresolvedReferences
		"""Given a hand of cards, return a snapshot of the first card and the last card in the hand.

		Examples
		--------
		>>> result = HandSnapshotTuple.of_hand([Card.Jack_of_Hearts, Card.Queen_of_Clubs, Card.Three_of_Spades])
		>>> result[0] is Suit.Hearts
		True
		>>> result[1] is Suit.Spades
		True
		"""

		# noinspection PyArgumentList
		return cls(first_card_suit=hand[0].suit, last_card_suit=hand[-1].suit)


class RoundScoreTuple(NamedTuple):
	"""A tuple giving detailed information regarding the points a player won in a specific round."""

	tricks_bid: ValidBid
	tricks_won: PossibleTricksWinnings
	points_won: int
	cumulative_points: int


class ClientPlayersMeta(PlayersMeta):
	"""Metaclass to support the `ClientPlayers` class.

	All methods in this metaclass *could* be implemented as `classmethod`s in the `ClientPlayers` class,
	but have been implemented in an extension of the metaclass for consistency's sake.
	(In the abstract `Players` class, all methods operating on the class are separated into the metaclass.)
	"""

	_all_players_list: [list[ClientPlayer]]
	_all_players_dict: [dict[str, ClientPlayer]]

	def me(cls: type[P]) -> P:
		"""Return the player representing the client."""
		return cls(rc.playerindex)

	@property
	def scoreboard_this_round(cls, /) -> list[RoundScoreTuple]:
		"""Return a `list` of `RoundScoreTuple` `NamedTuple`s, each representing one player's score this round."""
		return [player.scoreboard_data for player in cls]

	def _all_equal_by_attribute(cls, attr: str, /) -> bool:
		# noinspection PyUnresolvedReferences
		"""Return `True` if all players in the game are equal relative to a certain attribute, else `False`.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=3)
		>>> Alex, Jane, Charlotte = ClientPlayers.make_players(names=('Alex', 'Jane', 'Charlotte'))
		>>> ClientPlayers._all_equal_by_attribute('points')
		True
		>>> Alex.points = 5
		>>> ClientPlayers._all_equal_by_attribute('points')
		False
		"""

		g = groupby(cls, key=attrgetter(attr))
		return next(g, True) and not next(g, False)

	def scoreboard_text(
			cls,
			/,
			*,
			linesize: int,
			start_y: int,
			surf_width: float,
			left_margin: int,
			attribute: ScoreboardTextKeys
	) -> list[LineOfScoreboardText]:
		"""Return a `list` of `LineOfScoreboardText` `NamedTuple`s, describing the scoreboard text to be blitted.

		Parameters
		----------
		linesize: int
			The size of the pygame font being used.

		start_y: int
			The y-coordinate at which the first line of scoreboard text will be blitted.

		surf_width: float
			The width of the Scoreboard surface.

		left_margin: int
			The x-coordinate at which the left side of the text will be aligned.

		attribute: ScoreboardTextKeys
			This function is called twice:
			once to determine arguments required for blitting the top half of the scoreboard,
			and once to determine arguments required for blitting the bottom half of the scoreboard.

			This parameter -- which can be one of two "keys" -- determines which situation we are in.
		"""

		sorted_players = getattr(cls, f'sorted_by_{attribute}_descending')
		right_align_x = surf_width - left_margin
		scoreboard_text_args_list = []

		for i, player in enumerate(sorted_players):
			scoreboard_text_args_list += player.scoreboard_text_helper(
				y_coordinate=(start_y + (linesize * i)),
				left_align_x=left_margin,
				right_align_x=right_align_x,
				attribute=attribute
			)

		return scoreboard_text_args_list

	def board_text(cls, args: BoardTextArgs, /, *, positions: Iterable[Position]) -> list[LineOfBoardText]:
		"""Return a `list` of `LineOfBoardText` `NamedTuple`s, describing the arguments required to blit the board text.

		Parameters
		----------
		args: BoardTextArgs
			A single `BoardTextArgs` `NamedTuple`, containing args required by `Player.board_text_helper.

		positions: `Iterable[Position]`
			An iterable of (x, y) `NamedTuple` coordinates,
			indicating the position where each player's board text needs to be blitted.
		"""

		all_bid = cls.all_bid
		board_text = []

		for player, pos in zip(cls, positions):
			board_text.append(player.board_text_helper(args=args, all_bid=all_bid, base_pos=pos))

		return board_text

	def bid_waiting_text(cls, /, player_index: int) -> str:
		# noinspection PyUnresolvedReferences
		"""Return a string describing how many players (if any) have yet to bid at the beginning of a round.

		Parameters
		----------
		player_index: int
			The player_index of the player using the programme.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=2)
		>>> Alex, Charlotte = ClientPlayers.make_players(names=('Alex', 'Charlotte'))
		>>> ClientPlayers.bid_waiting_text(0)
		'Waiting for Charlotte to bid'
		>>> ClientPlayers.reset_for_unit_test(player_number=3)
		>>> Alex, Charlotte, Jane = ClientPlayers.make_players(names=('Alex', 'Charlotte', 'Jane'))
		>>> ClientPlayers.bid_waiting_text(0)
		'Waiting for 3 remaining players to bid'
		>>> Alex.bids(5)
		>>> Charlotte.bids(3)
		>>> ClientPlayers.bid_waiting_text(0)
		'Waiting for Jane to bid'
		"""

		if rc.player_number == 2:
			waiting_text = cls(0 if player_index else 1).name
		elif (players_not_bid := sum(1 for player in cls if not player.has_bid)) > 1:
			waiting_text = f'{players_not_bid} remaining players'
		else:
			waiting_text = next(player for player in cls if not player.has_bid).name
		return f'Waiting for {waiting_text} to bid'

	# Keeping this as a regular method rather than a `property`
	# in order to keep it consistent with the other text-iterator methods,
	# some of which require arguments.
	def bid_text(cls, /) -> StringIterator:
		# noinspection PyUnresolvedReferences
		"""Iterate through a sequence of strings describing each player's bid at the start of a round.
		Bids will be announced in order from the highest bidder to the lowest bidder.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=3)
		>>> Alex, Jane, Charlotte = ClientPlayers.make_players(names=('Alex', 'Jane', 'Charlotte'))
		>>> Alex.bids(2)
		>>> Charlotte.bids(1)
		>>> Jane.bids(5)
		>>> for message in ClientPlayers.bid_text():
		...     print(message)
		...
		All players have now bid.
		Jane bids 5.
		Alex bids 2.
		Charlotte bids 1.
		>>> Alex.bids(5)
		>>> Charlotte.bids(5)
		>>> for message in ClientPlayers.bid_text():
		...     print(message)
		...
		All players have now bid.
		All players bid 5.
		>>> rc.player_number = 2
		>>> del ClientPlayers._all_players_dict['Jane']
		>>> for message in ClientPlayers.bid_text():
		...     print(message)
		...
		Both players have now bid.
		Both players bid 5.
		"""

		yield f'{"All" if rc.player_number != 2 else "Both"} players have now bid.'

		if cls._all_equal_by_attribute('bid'):
			bid_number = cls(0).bid
			first_word = 'Both' if rc.player_number == 2 else 'All'
			yield f'{first_word} players bid {bid_number}.'
		else:
			sorted_players = sorted(cls, key=attrgetter('bid'), reverse=True)
			players_in_twos: Iterator[tuple[ClientPlayer, Optional[ClientPlayer]]]

			players_in_twos = zip(
				sorted_players,
				chain([None], sorted_players)
			)

			for player, previous_player in players_in_twos:
				injection = " also" if previous_player is not None and player.bid == previous_player.bid else ""
				yield f'{player.name}{injection} bids {player.bid}.'

	def end_of_round_text(cls, /, *, final_round: bool) -> StringIterator:
		# noinspection PyUnresolvedReferences
		"""Iterate through a sequence of strings summarising how many points each player won in the round just played.

		Parameters
		----------
		final_round: bool
			`True` if the final round of the game has just been played, else `False`.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=2)
		>>> Alex, Charlotte = ClientPlayers.make_players(names=('Alex', 'Charlotte'))
		>>> for message in ClientPlayers.end_of_round_text(final_round=False):
		...     print(message)
		...
		Round has ended.
		Both players won 0 points.
		>>> rc.player_number = 3
		>>> Jane = ClientPlayer()
		>>> Jane.name = 'Jane'
		>>> Jane.points_last_round = 1
		>>> for message in ClientPlayers.end_of_round_text(final_round=False):
		...     print(message)
		...
		Round has ended.
		Jane won 1 point.
		Alex won 0 points.
		Charlotte won 0 points.
		>>> Alex.points_last_round = 1
		>>> Charlotte.points_last_round = 1
		>>> Jane.points = 5
		>>> Alex.points = 7
		>>> for message in ClientPlayers.end_of_round_text(final_round=True):
		...     print(message)
		...
		Round has ended.
		All players won 1 point.
		--- END OF GAME SCORES ---
		Alex leads with 7 points.
		Jane has 5 points.
		Charlotte brings up the rear with 0 points.
		"""

		yield 'Round has ended.'

		if cls._all_equal_by_attribute('points_last_round'):
			points = cls(0).points_last_round

			yield ''.join((
				("Both" if rc.player_number == 2 else "All"),
				' players won ',
				f'{points} point{"s" if points != 1 else ""}.'
			))

		else:
			for player in sorted(cls, key=attrgetter('points_last_round'), reverse=True):
				yield f'{player.name} won {(points := player.points_last_round)} point{"s" if points != 1 else ""}.'

		if final_round:
			yield '--- END OF GAME SCORES ---'

			sorted_players = cls.sorted_by_scores_descending
			players_in_threes: Iterator[tuple[ClientPlayer, Optional[ClientPlayer], Optional[ClientPlayer]]]

			players_in_threes = zip(
				sorted_players,
				chain([None], sorted_players),
				chain(sorted_players[1:], [None])
			)

			for player, previous_player, next_player in players_in_threes:
				points = player.points

				if previous_player is None and points != next_player.points:
					verb = 'leads with'
				elif next_player is None and points != previous_player.points:
					verb = 'brings up the rear with'
				else:
					verb = 'has'

				also_needed = (previous_player is not None and points == previous_player.points)
				ending = "s" if points != 1 else ""
				yield f'{player.name} {"also " if also_needed else ""}{verb} {points} point{ending}.'

	# Keeping this as a regular method rather than a `property`
	# in order to keep it consistent with the other text-iterator methods,
	# some of which require arguments.
	def end_of_game_text(cls, /) -> StringIterator:
		# noinspection PyUnresolvedReferences
		"""Iterate through a sequence of strings that summarise the state of play at the end of the game.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=3)
		>>> Alex, Jane, Charlotte = ClientPlayers.make_players(names=('Alex', 'Jane', 'Charlotte'))
		>>> for message in ClientPlayers.end_of_game_text():
		...     print(message)
		...
		Tied game!
		The joint winners of this game were Alex, Jane and Charlotte, with 0 points each!
		>>> Alex.points = 10
		>>> for message in ClientPlayers.end_of_game_text():
		...     print(message)
		...
		Alex won the game!
		>>> Jane.points = 10
		>>> for message in ClientPlayers.end_of_game_text():
		...     print(message)
		...
		Tied game!
		The joint winners of this game were Alex and Jane, with 10 points each!
		"""

		max_points = max(player.points for player in cls)
		winners = [player for player in cls if get_points(player) == max_points]

		for player in winners:
			player.games_won += 1

		if winner_no := len(winners) == 1:
			yield f'{winners[0].name} won the game!'
		else:
			if winner_no == 2:
				winners_list = f'{winners[0].name} and {winners[1].name}'
			else:
				winners_list = f'{", ".join([winner.name for winner in winners[:-1]])} and {winners[-1].name}'

			yield 'Tied game!'
			yield f'The joint winners of this game were {winners_list}, with {max_points} points each!'

	# Keeping this as a regular method rather than a `property`
	# in order to keep it consistent with the other text-iterator methods,
	# some of which require arguments.
	def tournament_leaders_text(cls, /) -> StringIterator:
		# noinspection PyUnresolvedReferences
		"""Iterate through a sequence of strings that summarise who has won the most games at the end of a game.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=3)
		>>> Alex, Jane, Charlotte = ClientPlayers.make_players(names=('Alex', 'Jane', 'Charlotte'))
		>>> for message in ClientPlayers.tournament_leaders_text():
		...     print(message)
		...
		In this tournament, Alex has won 0 games so far.
		Jane has also won 0 games so far.
		Charlotte has also won 0 games so far.
		>>> Alex.games_won = 1
		>>> for message in ClientPlayers.tournament_leaders_text():
		...     print(message)
		...
		In this tournament, Alex has won 1 game so far.
		Jane has won 0 games so far.
		Charlotte has also won 0 games so far.
		Alex leads so far in this tournament, having won 1 game!
		>>> Charlotte.games_won = 1
		>>> for message in ClientPlayers.tournament_leaders_text():
		...     print(message)
		...
		In this tournament, Alex has won 1 game so far.
		Charlotte has also won 1 game so far.
		Jane has won 0 games so far.
		Alex and Charlotte lead so far in this tournament, having won 1 game each!
		"""

		max_games_won = max(player.games_won for player in cls)
		leaders = [player for player in cls if player.games_won == max_games_won]
		sorted_players = cls.sorted_by_games_won_descending

		for p, player in enumerate(sorted_players):
			part1 = "In this tournament, " if not p else ""
			part2 = "also " if p and player.games_won == sorted_players[p - 1].games_won else ""
			plural = "s" if player.games_won != 1 else ""
			yield f'{part1}{player.name} has {part2}won {player.games_won} game{plural} so far.'

		if len(leaders) != rc.player_number:
			games_won_text = f'having won {max_games_won} game{"s" if max_games_won > 1 else ""}'

			if (winner_number := len(leaders)) == 1:
				yield f'{leaders[0].name} leads so far in this tournament, {games_won_text}!'

			elif winner_number == 2:
				yield f'{leaders[0].name} and {leaders[1].name} lead so far in this tournament, {games_won_text} each!'

			else:
				joined_list = ", ".join(leader.name for leader in leaders[:-1])
				last = leaders[-1].name
				yield f'{joined_list} and {last} lead so far in this tournament, {games_won_text} each!'

	def end_of_game(cls, /) -> None:
		# noinspection PyUnresolvedReferences
		"""Reset all `Players` objects at the end of the game, in prepraration for the next game.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=3)
		>>> p0, p1, p2 = ClientPlayers.make_players()
		>>> p0.points = 3
		>>> p1.points = 5
		>>> [p.points for p in ClientPlayers]
		[3, 5, 0]
		>>> ClientPlayers.end_of_game()
		>>> [p.points for p in ClientPlayers]
		[0, 0, 0]
		"""

		super().end_of_game()
		for player in cls:
			player.points = 0

	@property
	def sorted_by_scores_descending(cls: type[P], /) -> list[P]:
		# noinspection PyUnresolvedReferences
		"""Get a `list` containing all players, sorted from highest-scoring to lowest-scoring.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=2)
		>>> Alex, Charlotte = ClientPlayers.make_players(names=('Alex', 'Charlotte'))
		>>> Alex.points = 10
		>>> Charlotte.points = 20
		>>> [player.name for player in ClientPlayers.sorted_by_scores_descending]
		['Charlotte', 'Alex']
		>>> Alex.points = 30
		>>> [player.name for player in ClientPlayers.sorted_by_scores_descending]
		['Alex', 'Charlotte']
		"""

		return sorted(cls, key=get_points, reverse=True)

	@property
	def sorted_by_games_won_descending(cls: type[P], /) -> list[P]:
		# noinspection PyUnresolvedReferences
		"""Get a `list` containing all players, sorted from most games won to least games won.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=2)
		>>> Alex, Charlotte = ClientPlayers.make_players(names=('Alex', 'Charlotte'))
		>>> Alex.games_won += 1
		>>> [player.name for player in ClientPlayers.sorted_by_games_won_descending]
		['Alex', 'Charlotte']
		>>> Charlotte.games_won += 2
		>>> [player.name for player in ClientPlayers.sorted_by_games_won_descending]
		['Charlotte', 'Alex']
		"""

		return sorted(cls, reverse=True, key=attrgetter('games_won'))

	@property
	def highest_scorer(cls: type[P], /) -> P:
		# noinspection PyUnresolvedReferences
		"""Get the player who currently has the highest score.

		Examples
		--------
		>>> ClientPlayers.reset_for_unit_test(player_number=2)
		>>> Alex, Charlotte = ClientPlayers.make_players(names=('Alex', 'Charlotte'))
		>>> Alex.points = 10
		>>> ClientPlayers.highest_scorer is Alex is ClientPlayers['Alex'] is ClientPlayer(0)
		True
		>>> Charlotte.points = 20
		>>> ClientPlayers.highest_scorer is Charlotte is ClientPlayers['Charlotte'] is ClientPlayer(1)
		True
		"""

		return max(cls, key=get_points)


class ClientPlayer(AbstractPlayer, metaclass=ClientPlayersMeta):
	"""Object representing a single player in the game on the clientside.

	This class represents the abstract concept of a player,
	and also has some methods relating to the mechanics
	of displaying player-related information on the screen using pygame.
	"""

	__slots__ = {
		'points':               'The number of points the player has currently in this game, an integer >= 0.',
		'games_won':            'The number of games the player has won so far in this tournament, an integer >= 0.',
		'scoreboard_data':      "A list of integers representing the player's score this round.",
		'round_leader':         "A boolean value: `True` if the player leads this round, else `False`.",
		'tricks_this_round':    'The number of tricks the player has won this round, an int in range 0 <= x <= 13.',
		'points_last_round':    'The number of points the player scored last round, an integer in range 0 <= x <= 23.',
		'_pos_in_trick':        '<Description goes here>'
	}

	NON_REPR_SLOTS: ClassVar = frozenset({'scoreboard_data'})
	EXTRA_REPR_ATTRS: ClassVar = ('pos_in_trick',)

	points: int
	games_won: int
	_pos_in_trick: TrickPosition
	scoreboard_data: RoundScoreTuple
	round_leader: bool
	tricks_this_round: PossibleTricksWinnings
	points_last_round: PossiblePointsScored

	def __init__(self, /) -> None:
		super().__init__()
		self.points = 0
		self.games_won = 0
		self.round_leader = False
		self.tricks_this_round = 0
		self.points_last_round = 0
		self._pos_in_trick = TrickPosition.POSITION_NOT_YET_KNOWN

		self.scoreboard_data = RoundScoreTuple(
			tricks_bid=Placeholders.NOT_YET_BID,
			tricks_won=0,
			points_won=0,
			cumulative_points=0
		)

	@property
	def pos_in_trick(self, /) -> TrickPosition:
		"""Get the player's position in the trick."""
		return self._pos_in_trick

	@pos_in_trick.setter
	def pos_in_trick(self, pos: int, /) -> None:
		"""Set the player's position in the trick."""
		self._pos_in_trick = TrickPosition(pos)

	@pos_in_trick.deleter
	def pos_in_trick(self, /) -> None:
		"""Reset this attribute to the placeholder value."""
		self._pos_in_trick = TrickPosition.POSITION_NOT_YET_KNOWN

	def scoreboard_text_helper(
			self,
			/,
			*,
			y_coordinate: int,
			left_align_x: float,
			right_align_x: float,
			attribute: ScoreboardTextKeys
	) -> list[LineOfScoreboardText]:
		"""Return a `list` of `LineOfScoreboardText` `NamedTuple`s, describing this player's specific scoreboard text.

		Parameters
		----------
		y_coordinate: `int`
			An `int` indicating the y-coordinate at which the top line of the text will be blitted at,
			relative to the Scoreboard surface.

		left_align_x: `float`
			A `float` indicating the x-coordinate at which the left side of the text will be blitted at,
			relative to the Scoreboard surface.

		right_align_x: `float`
			A `float` indicating the x-coordinate at which the right side of the text will be blitted at,
			relative to the Scoreboard surface.

		attribute: `ScoreboardTextKeys`
			This function is called twice:
			once to determine arguments required for blitting the top half of the scoreboard,
			and once to determine arguments required for blitting the bottom half of the scoreboard.

			This parameter -- which can be one of two "keys" -- determines which situation we are in.
		"""

		scoreboard_text_line1 = LineOfScoreboardText(
				text=f'{self}:',
				position_kwargs={TextAlignment.TOP_LEFT_ALIGN: Position(left_align_x, y_coordinate)}
			)

		value = self.points if attribute is ScoreboardTextKeys.CURRENT_SCORES else self.games_won

		scoreboard_text_line2 = LineOfScoreboardText(
				text=f'{value} {attribute}{"s" if value != 1 else ""}',
				position_kwargs={TextAlignment.TOP_RIGHT_ALIGN: Position(right_align_x, y_coordinate)}
			)

		return [scoreboard_text_line1, scoreboard_text_line2]

	def board_text_helper(self, /, *, args: BoardTextArgs, all_bid: bool, base_pos: Position) -> list[LineOfBoardText]:
		"""Return a `list` of `LineOfBoardText` `NamedTuple`s, describing this player's specific board text.

		Parameters
		----------
		args: `BoardTextArgs`
			A `NamedTuple` containing information on the player_index for the player whose turn it is (`int`),
			whether a trick is currently in progress (`bool`),
			how many cards have been played so far this trick (`int`), the linesize of the font being used (`float`),
			and the player_index of the player leading this round(`int`).

		all_bid: `bool`
			`True` if all players have bid yet, else `False`.

		base_pos: `Position`
			An (x, y) `NamedTuple` describing the top-left coordinate for where the text needs to start.
		"""

		whose_turn, trick_in_progress, played_cards_no, linesize, round_leader_index = args
		base_x, base_y = base_pos
		condition = (whose_turn == self.player_index and trick_in_progress and played_cards_no < rc.player_number)
		font = BoardSurfFonts.UNDERLINED_BOARD_FONT if condition else BoardSurfFonts.STANDARD_BOARD_FONT

		board_text_line1 = LineOfBoardText(text=f'{self}', font_name=font, position=Position(base_x, base_y))

		if (bid := self.bid) == -1:
			bid_text = 'bid unknown'
		elif all_bid:
			bid_text = f'bid {bid}'
		else:
			bid_text = f'bid received'

		board_text_line2 = LineOfBoardText(
				text=bid_text,
				font_name=BoardSurfFonts.STANDARD_BOARD_FONT,
				position=Position(base_x, (base_y + linesize))
			)

		tricks = f'{self.tricks_this_round} trick{"" if self.tricks_this_round == 1 else "s"}'

		board_text_line3 = LineOfBoardText(
				text=tricks,
				font_name=BoardSurfFonts.STANDARD_BOARD_FONT,
				position=Position(base_x, (base_y + (linesize * 2)))
			)

		player_text = [board_text_line1, board_text_line2, board_text_line3]

		if self.player_index == round_leader_index and not all_bid:
			board_text_line4 = LineOfBoardText(
					text='Leads this round',
					font_name=BoardSurfFonts.STANDARD_BOARD_FONT,
					position=Position(base_x, (base_y + (linesize * 3)))
			)

			player_text.append(board_text_line4)

		return player_text

	def receives_cards(self: P, cards: Iterable[Card], /, *, trumpsuit: Suit) -> P:
		"""Receive a new hand of cards at the start of a round. Sort the cards upon receiving them.
		See base class for full description of parameters.
		"""

		hand = self._hand
		hand.extend(cards)
		sort_hand_in_place.after_new_deal(hand=hand, trumpsuit=trumpsuit)

		for card in cards:
			card.AddToHand(self.name)

		return self

	def plays_card(self, card: Card, /, *, trumpsuit: Suit) -> None:
		"""Play a card in a trick, removing it from the player's hand, possibly causing the hand to be resorted.

		Parameters
		----------
		card: a `Card` object (see the `cards` module).
			The card the player is playing.

		trumpsuit: Suit (see the `Suit` module).
			Removing a card from the player's hand may mean that the hand needs to be resorted.
			The trumpsuit is relevant to the way the hand is sorted, as the trump is usually on the left of the hand.
		"""

		hand = self._hand
		hand_snapshot = HandSnapshotTuple.of_hand(hand)
		hand.remove(card)

		sort_hand_in_place.after_playing_a_card(
			hand=hand,
			trumpsuit=trumpsuit,
			played_suit=card.suit,
			hand_snapshot=hand_snapshot
		)

	def end_of_round(self: P, /) -> P:
		"""Reset and adjust various attributes in prepration for the next round."""

		bid_this_round, tricks_this_round = self.bid, self.tricks_this_round

		# Have to redefine points_this_round variable in order to redefine points_last_round correctly.
		points_this_round = tricks_this_round + (10 if bid_this_round == tricks_this_round else 0)
		self.points += points_this_round
		self.scoreboard_data = RoundScoreTuple(bid_this_round, tricks_this_round, points_this_round, self.points)
		del self.bid

		# Have to redefine points_last_round variable for some of the text-generator methods in the metaclass.
		self.points_last_round = cast(PossiblePointsScored, points_this_round)
		self.tricks_this_round = 0
		return self

	def move_colliderects_of_hand(self, /, *, x_motion: float, y_motion: float) -> None:
		"""Move all cards in the player's hand along a certain `(x, y)` vector."""

		for card in self._hand:
			card.move_colliderect(x_motion, y_motion)


# Alias so we can have more natural syntax when iterating all over players -- `for player in Players` etc.
ClientPlayers = ClientPlayer


if __name__ == '__main__':
	from doctest import testmod
	testmod()
