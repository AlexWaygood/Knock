from pandas import DataFrame, concat
from src.players.players_client import ClientPlayer as Player


# noinspection PyAttributeOutsideInit
class Scoreboard:
	__slots__ = 'PlayerNoTimes4', 'ColumnNo', 'Initialised', 'names', 'columns', 'StartNo', 'scoreboard', \
	            'DisplayScoreboard'

	def __init__(self) -> None:
		self.Initialised = False
		self.PlayerNoTimes4 = Player.PlayerNo * 4
		self.ColumnNo = self.PlayerNoTimes4 + 2

	def SetUp(self, StartCardNumber: int) -> None:
		self.names = Player.GetNames()
		self.columns = ['', ''] + sum((['', name, '', ''] for name in self.names), start=[])
		self.StartNo = StartCardNumber

		self.scoreboard = DataFrame(
			[['Round', 'Cards'] + sum((['Bid', 'Won', 'Points', 'Score'] for _ in self.names), start=[])],
			columns=self.columns
		)

		self.DisplayScoreboard = self.FillBlanks(0)
		self.Initialised = True

	def UpdateScores(self, RoundNumber: int, CardNumber: int) -> None:
		NewRow = DataFrame(
			[[RoundNumber, CardNumber] + Player.ScoreboardThisRound()],
			columns=self.columns
		)

		self.scoreboard = concat(self.scoreboard, NewRow, ignore_index=True)
		self.DisplayScoreboard = self.FillBlanks(RoundNumber)

	def FillBlanks(self, RoundNumber: int) -> DataFrame:
		Blanks = DataFrame([
			([x, y] + [None for _ in range(self.PlayerNoTimes4)])

			for x, y in zip(
				range((RoundNumber + 1), (self.StartNo + 1)),
				range((self.StartNo - RoundNumber), 0, -1)
			)
		])

		return concat((self.scoreboard, Blanks), ignore_index=True)
