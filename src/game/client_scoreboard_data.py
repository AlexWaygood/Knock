from __future__ import annotations
from typing import TYPE_CHECKING
from pandas import DataFrame, concat

if TYPE_CHECKING:
	from src.players.players_client import ClientGameplayers as Gameplayers


# noinspection PyAttributeOutsideInit
class Scoreboard:
	__slots__ = 'players', 'PlayerNoTimes4', 'ColumnNo', 'Initialised', 'names', 'columns', 'StartNo', 'scoreboard', \
	            'DisplayScoreboard'

	def __init__(self, gameplayers: Gameplayers):
		self.Initialised = False
		self.players = gameplayers
		self.PlayerNoTimes4 = gameplayers.PlayerNo * 4
		self.ColumnNo = self.PlayerNoTimes4 + 2

	def SetUp(self, StartCardNumber):
		self.names = [f'{player}' for player in self.players]
		self.columns = ['', ''] + sum((['', name, '', ''] for name in self.names), start=[])
		self.StartNo = StartCardNumber

		self.scoreboard = DataFrame(
			[['Round', 'Cards'] + sum((['Bid', 'Won', 'Points', 'Score'] for _ in self.names), start=[])],
			columns=self.columns
		)

		self.DisplayScoreboard = self.FillBlanks(0)
		self.Initialised = True

	def UpdateScores(self, RoundNumber, CardNumber):
		NewRow = DataFrame(
			[[RoundNumber, CardNumber] + sum((player.Scoreboard for player in self.players), start=[])],
			columns=self.columns
		)

		self.scoreboard = concat(self.scoreboard, NewRow, ignore_index=True)
		self.DisplayScoreboard = self.FillBlanks(RoundNumber)

	def FillBlanks(self, RoundNumber: int):
		Blanks = DataFrame([
			([x, y] + [None for _ in range(self.PlayerNoTimes4)])

			for x, y in zip(
				range((RoundNumber + 1), (self.StartNo + 1)),
				range((self.StartNo - RoundNumber), 0, -1)
			)
		])

		return concat((self.scoreboard, Blanks), ignore_index=True)
