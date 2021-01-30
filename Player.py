from PlayerHandSort import SortHand
from collections import UserList
from HelperFunctions import AllEqual
from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


class Gameplayers(UserList):
	__slots__ = 'data', 'players', 'PlayerNumber', 'Scoreboard'

	def __init__(self, *players):
		super().__init__()
		self.data = list(players)
		self.players = self.data
		self.PlayerNo = 0
		self.Scoreboard = []

	def __getitem__(self, key):
		try:
			return self.players[key]
		except:
			try:
				return next(player for player in self.players if player.name == key)
			except StopIteration:
				raise IndexError

	def __iter__(self):
		return iter(self.players)

	def NextStage(self):
		self.players = [player.NextStage() for player in self.players]

	def WaitForPlayers(self):
		while any(not player.ActionComplete for player in self.players):
			delay(1)

		self.NextStage()

	def RoundCleanUp(self, StartNo=0, RoundNumber=0, server=False):
		self.players = [player.EndOfRound(StartNo, RoundNumber, server) for player in self.players]

		if not server:
			self.Scoreboard.append(sum((player.Scoreboard for player in self.players), start=[]))

	def HighestScoreFirst(self):
		return sorted(self.players, key=Player.GetPoints, reverse=True)

	def MostGamesWonFirst(self):
		return sorted(self.players, reverse=True, key=lambda player: player.GamesWon)

	def AllPlayersHaveJoinedTheGame(self):
		return all(isinstance(player.name, str) for player in self.players) and len(self.players) == self.PlayerNo

	def UpdateFromServer(self, ServerPlayers):
		self.players = [player.ServerUpdate(ServerPlayers[player.name], JustBid=True) for player in self.players]

	def ReceiveCards(self, Pack, CardNo, trumpsuit):
		self.players = [player.ReceiveCards([Pack.pop() for i in range(CardNo)], trumpsuit) for player in self.players]

	def AllBid(self):
		return all(player.Bid != -1 for player in self.players)

	def GameWinner(self):
		return max(self.players, key=Player.GetPoints)

	def NewGame(self):
		self.players = self.data = self.players[1:] + self.players[:1]
		self.players = [player.ResetPlayer(self.PlayerNo) for player in self.players]

	def ScoreboardText(self):
		for player in self.HighestScoreFirst():
			yield f'{player}:', f'{player.Points} point{"s" if player.Points != 1 else ""}'

	def ScoreboardText2(self):
		for player in self.MostGamesWonFirst():
			yield f'{player}:', f'{player.GamesWon} game{"s" if player.GamesWon != 1 else ""}'

	def BoardSurfaceText(self, TextPositions, LineSize, WhoseTurnPlayerIndex,
	                     TrickInProgress, PlayedCardsNo, RoundLeaderIndex):

		AllBid = self.AllBid()
		AllBoardText = []

		for index, player in enumerate(self.players):
			condition = (WhoseTurnPlayerIndex == index and TrickInProgress and PlayedCardsNo < self.PlayerNo)
			font = 'UnderLine' if condition else 'Normal'
			Bid = f'Bid {"unknown" if (Bid := player.Bid) == -1 else (Bid if AllBid else "received")}'
			Tricks = f'{player.Tricks} trick{"" if player.Tricks == 1 else "s"}'

			BaseX, BaseY = Pos = TextPositions[index]
			Pos2, Pos3 = (BaseX, (BaseY + LineSize)), (BaseX, (BaseY + (LineSize * 2)))

			PlayerText = [(f'{player}', font, Pos), (Bid, 'Normal', Pos2), (Tricks, 'Normal', Pos3)]
			Condition = (index == RoundLeaderIndex and not AllBid)

			if Condition:
				PlayerText.append(('Leads this round', 'Normal', (BaseX, (BaseY + (LineSize * 3)))))

			AllBoardText += PlayerText

		return AllBoardText

	def BidWaitingText(self, playerindex):
		if self.PlayerNo != 2:
			if (PlayersNotBid := sum(1 for player in self.players if player.Bid == -1)) > 1:
				WaitingText = f'{PlayersNotBid} remaining players'
			else:
				WaitingText = next(f'{player}' for player in self.players if player.Bid == -1)
		else:
			WaitingText = f'{self.players[0 if playerindex else 1]}'

		return f'Waiting for {WaitingText} to bid'

	def BidText(self):
		yield f'{"All" if self.PlayerNo != 2 else "Both"} players have now bid.'

		if AllEqual(player.Bid for player in self.players):
			BidNumber = self.players[0].Bid
			FirstWord = 'Both' if self.PlayerNo == 2 else 'All'
			yield f'{FirstWord} players bid {BidNumber}.'
		else:
			SortedPlayers = sorted(self.players, key=lambda player: player.Bid, reverse=True)
			for i, player in enumerate(SortedPlayers):
				yield f'{player}{" also" if i and player.Bid == SortedPlayers[i - 1].Bid else ""} bids {player.Bid}.'

	def EndRoundText(self, FinalRound: bool):
		yield 'Round has ended.'

		if AllEqual(player.PointsLastRound for player in self.players):
			Points = self.players[0].PointsLastRound

			yield f'{"Both" if self.PlayerNo == 2 else "All"} players won ' \
			      f'{Points} point{"s" if Points != 1 else ""}.'

		else:
			for player in sorted(self.players, key=lambda player: player.PointsLastRound, reverse=True):
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
		MaxPoints = max(player.Points for player in self.players)
		Winners = [player.WinsGame() for player in self.players if player.Points == MaxPoints]

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
		MaxGamesWon = max(player.GamesWon for player in self.players)
		Leaders = [player for player in self.players if player.GamesWon == MaxGamesWon]

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

	def __eq__(self, other):
		return self.players == other.players


class Player(object):
	"""Class object for representing a single player in the game."""

	__slots__ = 'name', 'playerindex', 'Hand', 'Bid', 'Points', 'GamesWon', 'PointsThisRound', 'Tricks', 'RoundLeader', \
	            'HandIteration', 'ActionComplete', 'PointsLastRound', 'PosInTrick', 'Scoreboard'

	AllPlayers = Gameplayers()

	def __init__(self, playerindex):
		self.AllPlayers.append(self)
		self.name = playerindex
		self.playerindex = playerindex
		self.Hand = []
		self.Bid = -1
		self.Points = 0
		self.Tricks = 0
		self.PointsThisRound = 0
		self.PointsLastRound = 0
		self.GamesWon = 0
		self.RoundLeader = False
		self.ActionComplete = False
		self.HandIteration = 1
		self.PosInTrick = -1
		self.Scoreboard = []

	def NextStage(self):
		self.ActionComplete = False
		return self

	def ReceiveCards(self, cards, TrumpSuit):
		# Must receive an argument in the form of a list
		self.Hand = [card.AddToHand(self.name) for card in SortHand(cards, TrumpSuit)]
		self.HandIteration += 1
		return self

	def MakeBid(self, number):
		self.Bid = int(number)
		self.ActionComplete = True
		return self

	def PlayCard(self, card, TrumpSuit):
		SuitTuple = ((Hand := self.Hand)[0].ActualSuit, Hand[-1].ActualSuit)
		Hand.remove(card)
		Suit = card.ActualSuit
		self.Hand = SortHand(Hand, TrumpSuit, PlayedSuit=Suit, SuitTuple=SuitTuple)
		self.HandIteration += 1

	def WinsTrick(self):
		self.PointsThisRound += 1
		self.Tricks += 1
		return self

	def WinsGame(self):
		self.GamesWon += 1
		return self

	def GetPoints(self):
		return self.Points

	def EndOfRound(self, StartNo, RoundNo, server=False):
		"""To be used on both client and server sides"""

		self.HandIteration += 1

		if server:
			self.Bid = -1
			return self

		self.Scoreboard = [RoundNo, (StartNo - RoundNo + 1), self.Bid, self.Tricks]

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

	def ResetPlayer(self, PlayerNo):
		self.Points = 0
		self.playerindex = (self.playerindex + 1) if self.playerindex < (PlayerNo - 1) else 0
		return self

	def ServerUpdate(self, other, JustBid=False):
		self.Bid = other.Bid

		if JustBid:
			return self

		self.Hand = other.Hand
		self.HandIteration = other.HandIteration
		return self

	def __repr__(self):
		return self.name if isinstance(self.name, str) else f'Player with index {self.playerindex}, as yet unnamed'

	def __eq__(self, other):
		return self.name == other.name and self.HandIteration == other.HandIteration
