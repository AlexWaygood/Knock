from __future__ import annotations

from typing import TYPE_CHECKING
from operator import attrgetter
from itertools import groupby

from src.players.players_abstract import Gameplayers, Player

if TYPE_CHECKING:
	from src.game.client_game import ClientGame as Game


class ClientPlayer(Player):
	__slots__ = 'Points', 'GamesWon', 'PointsThisRound', 'Tricks', 'RoundLeader', 'PointsLastRound', 'PosInTrick', \
	            'Scoreboard'

	AllPlayers: Gameplayers[ClientPlayer]

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

	@classmethod
	def AllEqualByAttribute(cls, attr: str):
		g = groupby(cls.AllPlayers, key=attrgetter(attr))
		return next(g, True) and not next(g, False)

	@classmethod
	def GetNames(cls):
		return [f'{player}' for player in cls.AllPlayers]

	@classmethod
	def GetScoreboard(cls):
		return sum((player.Scoreboard for player in cls.AllPlayers), start=[])

	@classmethod
	def AddVars(cls, game: Game):
		cls.PlayerNo = game.PlayerNumber

	@classmethod
	def RoundCleanUp(cls):
		for player in cls.AllPlayers:
			player.EndOfRound()

	@classmethod
	def HighestScoreFirst(cls):
		return sorted(cls.AllPlayers, key=attrgetter('Points'), reverse=True)

	@classmethod
	def MostGamesWonFirst(cls):
		return sorted(cls.AllPlayers, reverse=True, key=attrgetter('GamesWon'))

	@classmethod
	def AllBid(cls):
		return all(player.Bid != -1 for player in cls.AllPlayers)

	@classmethod
	def GameWinner(cls):
		return max(cls.AllPlayers, key=attrgetter('Points'))

	@classmethod
	def ScoreboardText(
			cls,
			Linesize: int,
			StartY: int,
			SurfWidth: int,
			LMargin: int,
			attr: str
	):
		gen = cls.HighestScoreFirst if attr == 'point' else cls.MostGamesWonFirst
		RightAlignX = SurfWidth - LMargin

		return sum(
			(plr.scoreboardhelp((StartY + (Linesize * i)), LMargin, RightAlignX, attr) for i, plr in enumerate(gen())),
			start=[]
		)

	def scoreboardhelp(
			self,
			y: int,
			LeftAlignX: int,
			RightAlignX: int,
			attribute: str
	):
		value = self.Points if attribute == 'point' else self.GamesWon

		return [
			(f'{self}:', {'topleft': (LeftAlignX, y)}),
			(f'{value} {attribute}{"s" if value != 1 else ""}', {'topright': (RightAlignX, y)})
		]

	@classmethod
	def BidWaitingText(cls, playerindex: int):
		if cls.PlayerNo != 2:
			if (PlayersNotBid := sum(1 for player in cls.AllPlayers if player.Bid == -1)) > 1:
				WaitingText = f'{PlayersNotBid} remaining players'
			else:
				WaitingText = next(f'{player}' for player in cls.AllPlayers if player.Bid == -1)
		else:
			WaitingText = f'{cls.AllPlayers[0 if playerindex else 1]}'

		return f'Waiting for {WaitingText} to bid'

	@classmethod
	def BidText(cls):
		yield f'{"All" if cls.PlayerNo != 2 else "Both"} players have now bid.'

		if cls.AllEqualByAttribute('Bid'):
			BidNumber = cls.AllPlayers[0].Bid
			FirstWord = 'Both' if cls.PlayerNo == 2 else 'All'
			yield f'{FirstWord} players bid {BidNumber}.'
		else:
			SortedPlayers = sorted(cls.AllPlayers, key=attrgetter('Bid'), reverse=True)
			for i, player in enumerate(SortedPlayers):
				yield f'{player}{" also" if i and player.Bid == SortedPlayers[i - 1].Bid else ""} bids {player.Bid}.'

	@classmethod
	def EndRoundText(cls, FinalRound: bool):
		yield 'Round has ended.'

		if cls.AllEqualByAttribute('PointsLastRound'):
			Points = cls.AllPlayers[0].PointsLastRound

			yield f'{"Both" if cls.PlayerNo == 2 else "All"} players won ' \
			      f'{Points} point{"s" if Points != 1 else ""}.'

		else:
			for player in sorted(cls.AllPlayers, key=attrgetter('PointsLastRound'), reverse=True):
				yield f'{player} won {(Points := player.PointsLastRound)} point{"s" if Points != 1 else ""}.'

		if FinalRound:
			yield '--- END OF GAME SCORES ---'

			for i, player in enumerate(SortedPlayers := cls.HighestScoreFirst()):
				Points = player.Points

				if not i and Points != SortedPlayers[i + 1].Points:
					Verb = 'leads with'
				elif i == cls.PlayerNo - 1 and Points != SortedPlayers[i - 1].Points:
					Verb = 'brings up the rear with'
				else:
					Verb = 'has'

				AlsoNeeded = (bool(i) and Points == SortedPlayers[i - 1].Points)
				Ending = "s" if Points != 1 else ""
				yield f'{player} {"also " if AlsoNeeded else ""}{Verb} {Points} point{Ending}.'

	@classmethod
	def GameCleanUp(cls):
		MaxPoints = max(player.Points for player in cls.AllPlayers)
		Winners = [player.WinsGame() for player in cls.AllPlayers if player.Points == MaxPoints]

		if (WinnerNo := len(Winners)) > 1:
			if WinnerNo == 2:
				ListOfWinners = f'{Winners[0]} and {Winners[1]}'
			else:
				ListOfWinners = f'{", ".join(Winner.name for Winner in Winners[:-1])} and {Winners[-1]}'

			yield 'Tied game!'
			yield f'The joint winners of this game were {ListOfWinners}, with {MaxPoints} each!'

		else:
			yield f'{Winners[0].name} won the game!'

	@classmethod
	def TournamentLeaders(cls):
		MaxGamesWon = max(player.GamesWon for player in cls.AllPlayers)
		Leaders = [player for player in cls.AllPlayers if player.GamesWon == MaxGamesWon]

		for p, player in enumerate(SortedPlayers := cls.MostGamesWonFirst()):
			Part1 = "In this tournament, " if not p else ""
			Part2 = "also " if p and player.GamesWon == SortedPlayers[p - 1].GamesWon else ""
			Plural = "s" if player.GamesWon != 1 else ""
			yield f'{Part1}{player} has {Part2}won {player.GamesWon} game{Plural} so far.'

		if len(Leaders) != cls.PlayerNo:
			GamesWonText = f'having won {MaxGamesWon} game{"s" if MaxGamesWon > 1 else ""}'

			if (WinnerNumber := len(Leaders)) == 1:
				yield f'{Leaders[0]} leads so far in this tournament, {GamesWonText}!'

			elif WinnerNumber == 2:
				yield f'{Leaders[0]} and {Leaders[1]} lead so far in this tournament, {GamesWonText} each!'

			else:
				JoinedList = ", ".join(leader.name for leader in Leaders[:-1])
				Last = Leaders[-1]
				yield f'{JoinedList} and {Last} lead so far in this tournament, {GamesWonText} each!'

	def WinsTrick(self):
		self.PointsThisRound += 1
		self.Tricks += 1
		return self

	def WinsGame(self):
		self.GamesWon += 1
		return self

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

	def BoardText(
			self,
			WhoseTurn: int,
			TrickInProgress: bool,
			PlayedCardsNo: int,
			AllBid: bool,
			PlayerNo: int,
			LineSize: int,
			RoundLeaderIndex: int,
			BaseX: int,
			BaseY: int
	):

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

	def ReprInfo(self):
		return '\n'.join((
			super().ReprInfo(),
			f'PosInTrick: {self.PosInTrick}.Points: {self.Points}.Tricks: {self.Tricks}.',
			f'PointsThisRound: {self.PointsThisRound}. PointsLastRound: {self.PointsLastRound}.'
			f'GamesWon: {self.GamesWon}. RoundLeader: {self.RoundLeader}. '
		))
