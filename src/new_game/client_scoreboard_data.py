"""A class for recording data on players' bids and points scored each round."""

from __future__ import annotations

from pandas import DataFrame, concat
from src import config as rc
from src.players.players_client import ClientPlayer as Players
from typing import Sequence


class Scoreboard:
	"""A class that records the player's bids and scores each round.

	The purpose of recording such granular details
	is so that we can use `matplotlib` to display a full scoreboard during the game.

	However, this class knows NOTHING about the display aspects of teh scoreboard;
	its sole function is to record the necessary data.
	"""

	__slots__ = (
		'player_no_times_4', 'column_no', 'column_names', 'start_card_no', 'scoreboard', 'display_scoreboard'
	)

	column_names: Sequence[str]
	start_card_no: int
	scoreboard: DataFrame
	display_scoreboard: DataFrame

	def __init__(self, /, *, start_card_number: int) -> None:
		self.player_no_times_4 = player_no_times_4 = (rc.player_number * 4)
		self.column_no = player_no_times_4 + 2
		player_names = Players.names
		column_names = ('', '') + sum((('', name, '', '') for name in player_names), start=())
		self.column_names = column_names
		self.start_card_no = start_card_number

		self.scoreboard = DataFrame(
			[('Round', 'Cards') + sum((('bid', 'Won', 'points', 'Score') for _ in player_names), start=())],
			columns=column_names
		)

		self.display_scoreboard = self._fill_blanks(round_number=0)

	def update_scores(self, /, *, round_number: int, card_number: int) -> None:
		"""Update the scoreboard at the end of the round."""

		new_row = DataFrame(
			[(round_number, card_number) + sum(Players.scoreboard_this_round, start=())],
			columns=self.column_names
		)

		self.scoreboard = concat(self.scoreboard, new_row, ignore_index=True)
		self.display_scoreboard = self._fill_blanks(round_number=round_number)

	def _fill_blanks(self, /, *, round_number: int) -> DataFrame:
		"""Helper method that ensures that we have a number of blank rows in the pandas dataframe.
		Blank rows ensure that the table is formatted correctly on matplotlib.
		"""

		start_card_no = self.start_card_no

		blanks = DataFrame([
			([x, y] + [None for _ in range(self.player_no_times_4)])

			for x, y in zip(
				range((round_number + 1), (start_card_no + 1)),
				range((start_card_no - round_number), 0, -1)
			)
		])

		return concat((self.scoreboard, blanks), ignore_index=True)
