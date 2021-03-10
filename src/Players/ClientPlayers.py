from typing import Union, Iterable
from src.Players.AbstractPlayers import Gameplayers, Player
from itertools import groupby
from src.Display.InteractiveScoreboard import InteractiveScoreboard


class ClientGameplayers(Gameplayers):
	__slots__ = 'Scoreboard'

	def __init__(self):
		super().__init__()
		self.Scoreboard = None

	def InitialiseScoreboard(self, game):
		self.Scoreboard = InteractiveScoreboard(game)

	def RoundCleanUp(self):
		self.data = [player.EndOfRound() for player in self.data]
		self.Scoreboard.UpdateScores()

	def HighestScoreFirst(self):
		return sorted(self.data, key=ClientPlayer.GetPoints, reverse=True)

	def MostGamesWonFirst(self):
		return sorted(self.data, reverse=True, key=lambda player: player.GamesWon)

	def AllPlayersHaveJoinedTheGame(self):
		return all(isinstance(player.name, str) for player in self.data) and len(self.data) == self.PlayerNo

	def AllBid(self):
		return all(player.Bid != -1 for player in self.data)

	def GameWinner(self):
		return max(self.data, key=ClientPlayer.GetPoints)

	def BidWaitingText(self, playerindex: int):
		if self.PlayerNo != 2:
			if (PlayersNotBid := sum(1 for player in self.data if player.Bid == -1)) > 1:
				WaitingText = f'{PlayersNotBid} remaining players'
			else:
				WaitingText = next(f'{player}' for player in self.data if player.Bid == -1)
		else:
			WaitingText = f'{self.data[0 if playerindex else 1]}'

		return f'Waiting for {WaitingText} to bid'

	def BidText(self):
		yield f'{"All" if self.PlayerNo != 2 else "Both"} players have now bid.'

		if AllEqual(player.Bid for player in self.data):
			BidNumber = self.data[0].Bid
			FirstWord = 'Both' if self.PlayerNo == 2 else 'All'
			yield f'{FirstWord} players bid {BidNumber}.'
		else:
			SortedPlayers = sorted(self.data, key=lambda player: player.Bid, reverse=True)
			for i, player in enumerate(SortedPlayers):
				yield f'{player}{" also" if i and player.Bid == SortedPlayers[i - 1].Bid else ""} bids {player.Bid}.'

	def EndRoundText(self, FinalRound: bool):
		yield 'Round has ended.'

		if AllEqual(player.PointsLastRound for player in self.data):
			Points = self.data[0].PointsLastRound

			yield f'{"Both" if self.PlayerNo == 2 else "All"} players won ' \
			      f'{Points} point{"s" if Points != 1 else ""}.'

		else:
			for player in sorted(self.data, key=lambda player: player.PointsLastRound, reverse=True):
				yield f'{player} won {(Points := player.PointsLastRound)} point{"s" if Points != 1 else ""}.'

		if FinalRound:
			yield '--- END OF GAME SCORES ---'

			for i, player in enumerate(SortedPlayers := self.HighestScoreFirst()):
				Points = player.Points

				if not i and Points != SortedPlayers[i + 1].Points:
					Verb = 'leads with'
				elif i == self.PlayerNo - 1 and Points != SortedPlayers[i - 1].Points:
					Verb = 'brings up the rear with'
				else:
					Verb = 'has'

				AlsoNeeded = (bool(i) and Points == SortedPlayers[i - 1].Points)
				Ending = "s" if Points != 1 else ""
				yield f'{player} {"also " if AlsoNeeded else ""}{Verb} {Points} point{Ending}.'

	def GameCleanUp(self):
		MaxPoints = max(player.Points for player in self.data)
		Winners = [player.WinsGame() for player in self.data if player.Points == MaxPoints]

		if (WinnerNo := len(Winners)) > 1:
			if WinnerNo == 2:
				ListOfWinners = f'{Winners[0] and Winners[1]}'
			else:
				ListOfWinners = f'{", ".join(Winner.name for Winner in Winners[:-1])} and {Winners[-1]}'

			yield 'Tied game!'
			yield f'The joint winners of this game were {ListOfWinners}, with {MaxPoints} each!'

		else:
			yield f'{Winners[0].name} won the game!'

	def TournamentLeaders(self):
		MaxGamesWon = max(player.GamesWon for player in self.data)
		Leaders = [player for player in self.data if player.GamesWon == MaxGamesWon]

		for p, player in enumerate(SortedPlayers := self.MostGamesWonFirst()):
			Part1 = "In this tournament, " if not p else ""
			Part2 = "also " if p and player.GamesWon == SortedPlayers[p - 1].GamesWon else ""
			Plural = "s" if player.GamesWon != 1 else ""
			yield f'{Part1}{player} has {Part2}won {player.GamesWon} game{Plural} so far.'

		if len(Leaders) != self.PlayerNo:
			GamesWonText = f'having won {MaxGamesWon} game{"s" if MaxGamesWon > 1 else ""}'

			if (WinnerNumber := len(Leaders)) == 1:
				yield f'{Leaders[0]} leads so far in this tournament, {GamesWonText}!'

			elif WinnerNumber == 2:
				yield f'{Leaders[0]} and {Leaders[1]} lead so far in this tournament, {GamesWonText} each!'

			else:
				JoinedList = ", ".join(leader.name for leader in Leaders[:-1])
				Last = Leaders[-1]
				yield f'{JoinedList} and {Last} lead so far in this tournament, {GamesWonText} each!'


class ClientPlayer(Player):
	__slots__ = 'Points', 'GamesWon', 'PointsThisRound', 'Tricks', 'RoundLeader', 'PointsLastRound', 'PosInTrick', \
	            'Scoreboard'

	AllPlayers = ClientGameplayers()

	def __init__(self, playerindex: int):
		super().__init__(playerindex)
		self.PosInTrick = -1
		self.Scoreboard = []
		self.Points = 0
		self.Tricks = 0
		self.PointsThisRound = 0
		self.PointsLastRound = 0
		self.GamesWon = 0
		self.RoundLeader = False

	def MakeBid(self, number: Union[int, str]):
		self.Bid = int(number)
		return self

	def WinsTrick(self):
		self.PointsThisRound += 1
		self.Tricks += 1
		return self

	def WinsGame(self):
		self.GamesWon += 1
		return self

	def GetPoints(self):
		return self.Points

	def ResetPlayer(self, PlayerNo: int):
		super().ResetPlayer(PlayerNo)
		self.Points = 0
		return self

	def EndOfRound(self):
		self.Hand.Iteration += 1
		self.Scoreboard = [self.Bid, self.Tricks]

		# Have to redefine PointsThisRound variable in order to redefine PointsLastRound correctly.
		self.PointsThisRound += (10 if self.Bid == self.PointsThisRound else 0)
		self.Points += self.PointsThisRound
		self.Scoreboard += [self.PointsThisRound, self.Points]
		self.Bid = -1

		# Have to redefine PointsLastRound variable for some of the text-generator methods in the Gameplayers class.
		self.PointsLastRound = self.PointsThisRound
		self.PointsThisRound = 0
		self.Tricks = 0
		return self

	def BoardText(self, WhoseTurn, TrickInProgress, PlayedCardsNo, AllBid,
	                     PlayerNo, LineSize, RoundLeaderIndex, BaseX, BaseY):

		"""
		@type WhoseTurn: int
		@type TrickInProgress: bool
		@type PlayedCardsNo: int
		@type AllBid: bool
		@type PlayerNo: int
		@type LineSize: int
		@type RoundLeaderIndex: int
		@type BaseX: int
		@type BaseY: int
		"""

		condition = (WhoseTurn == self.playerindex and TrickInProgress and PlayedCardsNo < PlayerNo)
		font = 'UnderlinedBoardFont' if condition else 'StandardBoardFont'
		Bid = f'Bid {"unknown" if (Bid := self.Bid) == -1 else (Bid if AllBid else "received")}'
		Tricks = f'{self.Tricks} trick{"" if self.Tricks == 1 else "s"}'

		Pos2, Pos3 = (BaseX, (BaseY + LineSize)), (BaseX, (BaseY + (LineSize * 2)))

		PlayerText = [
			(f'{self}', font, (BaseX, BaseY)),
			(Bid, 'StandardBoardFont', Pos2),
			(Tricks, 'StandardBoardFont', Pos3)
		]

		Condition = (self.playerindex == RoundLeaderIndex and not AllBid)

		if Condition:
			PlayerText.append(('Leads this round', 'StandardBoardFont', (BaseX, (BaseY + (LineSize * 3)))))

		return PlayerText


def AllEqual(It: Iterable):
	"""Does what it says on the tin"""
	g = groupby(It)
	return next(g, True) and not next(g, False)
