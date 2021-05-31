from __future__ import annotations

from typing import TYPE_CHECKING, List
from operator import attrgetter
from itertools import groupby

import src.global_constants as gc

from src.players.players_abstract import Player, Hand

if TYPE_CHECKING:
	import src.special_knock_types as skt


class ClientPlayer(Player):
	__slots__ = 'Points', 'GamesWon', 'PointsThisRound', 'Tricks', 'RoundLeader', 'PointsLastRound', 'PosInTrick', \
	            'Scoreboard'

	_AllPlayers: skt.ClientPlayerList
	_AllPlayersDict: skt.ClientPlayerDict

	def __init__(self, playerindex: int) -> None:
		super().__init__(playerindex)
		self.PosInTrick = -1
		self.Scoreboard = []
		self.Points = 0
		self.Tricks = 0
		self.PointsThisRound = 0
		self.PointsLastRound = 0
		self.GamesWon = 0
		self.RoundLeader = False
		self.Hand = ClientHand()

	@classmethod
	def AllEqualByAttribute(cls, attr: str) -> bool:
		g = groupby(cls._AllPlayers, key=attrgetter(attr))
		return next(g, True) and not next(g, False)

	@classmethod
	def PlayerWinsTrick(cls, name: str) -> ClientPlayer:
		player = cls.player(name)
		player.PointsThisRound += 1
		player.Tricks += 1
		return player

	@classmethod
	def GetNames(cls) -> skt.PlayerNameList:
		return [str(player) for player in cls.iter()]

	@classmethod
	def ScoreboardThisRound(cls) -> List[int]:
		return sum((player.Scoreboard for player in cls.iter()), start=[])

	@classmethod
	def RoundCleanUp(cls) -> None:
		[player.EndOfRound() for player in cls.iter()]

	@classmethod
	def HighestScoreFirst(cls) -> skt.ClientPlayerList:
		return sorted(cls._AllPlayers, key=ClientPlayer.GetPoints, reverse=True)

	@classmethod
	def MostGamesWonFirst(cls) -> skt.ClientPlayerList:
		return sorted(cls._AllPlayers, reverse=True, key=attrgetter('GamesWon'))

	@classmethod
	def AllBid(cls) -> bool:
		return all(player.Bid != -1 for player in cls.iter())

	@classmethod
	def GameWinner(cls) -> ClientPlayer:
		return max(cls._AllPlayers, key=ClientPlayer.GetPoints)

	@classmethod
	def ScoreboardText(
			cls,
			Linesize: int,
			StartY: int,
			SurfWidth: float,
			LMargin: int,
			attr: str
	) -> skt.ScoreboardTextArgsList:

		gen = cls.HighestScoreFirst if attr == gc.SCOREBOARD_TEXT_KEY_1 else cls.MostGamesWonFirst
		RightAlignX = SurfWidth - LMargin

		return sum(
			(p.ScoreboardHelp((StartY + (Linesize * i)), LMargin, RightAlignX, attr) for i, p in enumerate(gen())),
			start=[]
		)

	def ScoreboardHelp(
			self,
			y: int,
			LeftAlignX: float,
			RightAlignX: float,
			attribute: str
	) -> skt.ScoreboardTextArgsList:

		value = self.Points if attribute == gc.SCOREBOARD_TEXT_KEY_1 else self.GamesWon

		return [
			(f'{self}:', {gc.TOP_LEFT_ALIGN: (LeftAlignX, y)}),
			(f'{value} {attribute}{"s" if value != 1 else ""}', {gc.TOP_RIGHT_ALIGN: (RightAlignX, y)})

		]

	@classmethod
	def BoardText(
			cls,
			*args,
			Positions: skt.PositionSequence = None
	) -> skt.StringFontPositionList:

		# Must receive exactly the same arguments as BoardHelp() method below
		AllBid = cls.AllBid()
		return sum((player.BoardHelp(*args, AllBid, *Positions[i]) for i, player in cls.enumerate()), start=[])

	def BoardHelp(
			self,
			WhoseTurn: int,
			TrickInProgress: bool,
			PlayedCardsNo: int,
			LineSize: int,
			RoundLeaderIndex: int,
			AllBid: bool,
			BaseX: int,
			BaseY: int
	) -> skt.StringFontPositionList:

		condition = (WhoseTurn == self.playerindex and TrickInProgress and PlayedCardsNo < self.PlayerNo)
		font = gc.UNDERLINED_BOARD_FONT if condition else gc.STANDARD_BOARD_FONT
		Bid = f'Bid {"unknown" if (Bid := self.Bid) == -1 else (Bid if AllBid else "received")}'
		Tricks = f'{self.Tricks} trick{"" if self.Tricks == 1 else "s"}'

		Pos2, Pos3 = (BaseX, (BaseY + LineSize)), (BaseX, (BaseY + (LineSize * 2)))

		PlayerText = [
			(f'{self}', font, (BaseX, BaseY)),
			(Bid, gc.STANDARD_BOARD_FONT, Pos2),
			(Tricks, gc.STANDARD_BOARD_FONT, Pos3)
		]

		Condition = (self.playerindex == RoundLeaderIndex and not AllBid)

		if Condition:
			PlayerText.append(('Leads this round', gc.STANDARD_BOARD_FONT, (BaseX, (BaseY + (LineSize * 3)))))

		return PlayerText

	@classmethod
	def BidWaitingText(cls, playerindex: int) -> str:
		if cls.PlayerNo == 2:
			WaitingText = f'{cls.player(0 if playerindex else 1)}'
		elif (PlayersNotBid := sum(1 for player in cls.iter() if player.Bid == -1)) > 1:
			WaitingText = f'{PlayersNotBid} remaining players'
		else:
			WaitingText = next(str(player) for player in cls.iter() if player.Bid == -1)
		return f'Waiting for {WaitingText} to bid'

	@classmethod
	def BidText(cls) -> skt.StringGenerator:
		yield f'{"All" if cls.PlayerNo != 2 else "Both"} players have now bid.'

		if cls.AllEqualByAttribute('Bid'):
			BidNumber = cls.player(0).Bid
			FirstWord = 'Both' if cls.PlayerNo == 2 else 'All'
			yield f'{FirstWord} players bid {BidNumber}.'
		else:
			SortedPlayers = sorted(cls._AllPlayers, key=attrgetter('Bid'), reverse=True)
			for i, player in enumerate(SortedPlayers):
				yield f'{player}{" also" if i and player.Bid == SortedPlayers[i - 1].Bid else ""} bids {player.Bid}.'

	@classmethod
	def EndRoundText(cls, FinalRound: bool) -> skt.StringGenerator:
		yield 'Round has ended.'

		if cls.AllEqualByAttribute('PointsLastRound'):
			Points = cls.player(0).PointsLastRound

			yield f'{"Both" if cls.PlayerNo == 2 else "All"} players won ' \
			      f'{Points} point{"s" if Points != 1 else ""}.'

		else:
			for player in sorted(cls._AllPlayers, key=attrgetter('PointsLastRound'), reverse=True):
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
	def GameCleanUp(cls) -> skt.StringGenerator:
		MaxPoints = max(player.Points for player in cls.iter())
		Winners = [player.WinsGame() for player in cls.iter() if player.Points == MaxPoints]

		if WinnerNo := len(Winners) == 1:
			yield f'{Winners[0].name} won the game!'
		else:
			if WinnerNo == 2:
				ListOfWinners = f'{Winners[0]} and {Winners[1]}'
			else:
				ListOfWinners = f'{", ".join([str(Winner) for Winner in Winners[:-1]])} and {Winners[-1]}'

			yield 'Tied game!'
			yield f'The joint winners of this game were {ListOfWinners}, with {MaxPoints} each!'

	@classmethod
	def TournamentLeaders(cls) -> skt.StringGenerator:
		MaxGamesWon = max(player.GamesWon for player in cls.iter())
		Leaders = [player for player in cls.iter() if player.GamesWon == MaxGamesWon]

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

	def GetPoints(self) -> int:
		return self.Points

	def WinsGame(self) -> ClientPlayer:
		self.GamesWon += 1
		return self

	def ResetPlayer(self, PlayerNo: int) -> ClientPlayer:
		super().ResetPlayer(PlayerNo)
		self.Points = 0
		return self

	def EndOfRound(self) -> ClientPlayer:
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

	def __repr__(self) -> str:
		return '\n'.join((
			super().__repr__(),
			f'PosInTrick: {self.PosInTrick}.Points: {self.Points}.Tricks: {self.Tricks}.',
			f'PointsThisRound: {self.PointsThisRound}. PointsLastRound: {self.PointsLastRound}.'
			f'GamesWon: {self.GamesWon}. RoundLeader: {self.RoundLeader}. '
		))


class ClientHand(Hand):
	__slots__ = tuple()

	# Used in gamesurf.py
	def MoveColliderects(self, XMotion: float, YMotion: float) -> None:
		[card.MoveColliderect(XMotion, YMotion) for card in self.data]
