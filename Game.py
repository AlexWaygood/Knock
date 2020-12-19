"""Class for encoding order of gameplay, in coordination with the client script."""

from random import shuffle
from itertools import chain, cycle

from Card import Card
from ClientClasses import *
from Player import Player

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


class Game(object):
	"""Class for encoding order of gameplay, in coordination with the client script."""

	__slots__ = 'StartCardPositions', 'CardPositions', 'RepeatGame', 'Attributes', 'GameAttributes', 'Triggers', \
	            'StartPlay'

	def __init__(self, PlayerNumber):
		self.StartCardPositions = [i for i in range(PlayerNumber)]
		self.CardPositions = self.StartCardPositions
		self.StartPlay = False
		self.RepeatGame = True
		self.Attributes = AttributeTracker(True, PlayerNumber)
		self.Triggers = Triggers()

	# A few functions to be accessed by the threaded-client function.

	@staticmethod
	def AddPlayerName(name, playerindex):
		Player.AllPlayers[playerindex].AddName(name)

	def TimeToStart(self):
		self.StartPlay = True

	@staticmethod
	def PlayerActionCompleted(playerindex):
		Player.AllPlayers[playerindex].ActionComplete = True

	def SetCardNumber(self, number):
		self.Attributes.Game['StartCardNumber'] = int(number)

	def PlayerMakesBid(self, playerindex, bid):
		Player.AllPlayers[playerindex].MakeBid(int(bid))
		self.Triggers.Surfaces['CurrentBoard'] += 1

	def ExecutePlay(self, cardID, playerindex):
		player = Player.AllPlayers[playerindex]
		card = next(card for card in player.Hand if card.ID == cardID)
		player.PlayCard(card, self.Attributes.Round['trumpsuit'])
		card.SetPos(self.CardPositions[len(self.Attributes.Trick['PlayedCards'])])
		self.Attributes.Trick['PlayedCards'].append(card)
		self.Triggers.Surfaces['CurrentBoard'] += 1

	def RepeatQuestionAnswer(self):
		self.RepeatGame = True

	# The remaining functions relate to the order of gameplay.

	def WaitForPlayers(self, attribute):
		self.Triggers.Events[attribute] += 1

		while any(not player.ActionComplete for player in Player.AllPlayers):
			delay(60)

		Player.AllPlayers = [player.NextStage() for player in Player.AllPlayers]

	def PlayGame(self):
		# Wait until the opening sequence is complete
		self.WaitForPlayers('GameInitialisation')

		WhichRound = range(1, (self.Attributes.Game['StartCardNumber'] + 1))
		HowManyCards = range(self.Attributes.Game['StartCardNumber'], 0, -1)
		WhoLeads = cycle(Player.AllPlayers)

		for roundnumber, cardnumber, RoundLeader in zip(WhichRound, HowManyCards, WhoLeads):
			self.PlayRound(roundnumber, cardnumber, RoundLeader)

		self.Attributes.Game['MaxPoints'] = max(player.Points for player in Player.AllPlayers)

		self.Attributes.Game['Winners'] = [
			player for player in Player.AllPlayers
			if player.Points == self.Attributes.Game['MaxPoints']
		]

		for player in self.Attributes.Game['Winners']:
			player.GamesWon += 1

		self.Triggers.Surfaces['Scoreboard'] += 1

		# Wait until all players have finished announcing the game winners.
		self.WaitForPlayers('WinnersAnnounced')

		if self.Attributes.Tournament['GamesPlayed']:
			self.Attributes.Tournament['MaxGamesWon'] = max(player.GamesWon for player in Player.AllPlayers)

			self.Attributes.Tournament['TournamentLeaders'] = [
				player for player in Player.AllPlayers
				if player.GamesWon == self.Attributes.Tournament['MaxGamesWon']
			]

			self.Triggers.Events['TournamentLeaders'] += 1

		self.RepeatGame = False

		while not self.RepeatGame:
			delay(1)

		self.NewGameReset()

		# Wait until all players have logged their new playerindex.
		self.WaitForPlayers('NewGameReset')

		self.PlayGame()

	def PlayRound(self, roundnumber, cardnumber, RoundLeader):
		self.Attributes.Round['CardNumberThisRound'] = cardnumber
		self.Attributes.Round['RoundNumber'] = roundnumber
		self.Attributes.Round['RoundLeader'] = RoundLeader
		RoundLeader.RoundLeader = True
		self.Triggers.Surfaces['Scoreboard'] += 1

		self.WaitForPlayers('RoundStart')

		# the trumpcard is set as part of this function call.
		self.NewPack()
		self.WaitForPlayers('NewPack')

		# Deal cards
		Pack, trumsuit = self.Attributes.Round['PackOfCards'], self.Attributes.Round['trumpsuit']

		Player.AllPlayers = [
			player.ReceiveCards([Pack.pop() for i in range(cardnumber)], trumsuit)
			for player in Player.AllPlayers
		]

		self.Triggers.Surfaces['TrumpCard'] += 1
		self.Triggers.Surfaces['CurrentBoard'] += 1
		self.WaitForPlayers('CardsDealt')

		FirstPlayer = RoundLeader
		RoundLeader.RoundLeader = False

		for i in range(cardnumber):
			FirstPlayerIndex = self.TrickStart(i + 1, FirstPlayer)
			self.TrickMiddle(FirstPlayerIndex)
			FirstPlayer = self.TrickEnd(self.Attributes.Trick['PlayedCards'])

		self.WaitForPlayers('RoundEnd')

		Player.AllPlayers = [player.ReceivePoints() for player in Player.AllPlayers]

		self.Triggers.Surfaces['Scoreboard'] += 1
		self.WaitForPlayers('PointsAwarded')

		Player.AllPlayers = [player.EndOfRound() for player in Player.AllPlayers]

		self.Attributes.Round['TrumpCard'] = None
		self.Attributes.Round['trumpsuit'] = ''

		if self.Attributes.Round['RoundNumber'] != self.Attributes.Game['StartCardNumber']:
			self.Attributes.Round['RoundNumber'] += 1
			self.Attributes.Round['CardNumberThisRound'] -= 1
			self.Attributes.Trick['TrickNumber'] = 1

		self.Triggers.Surfaces['CurrentBoard'] += 1
		self.Triggers.Surfaces['Scoreboard'] += 1

	def NewPack(self):
		PackOfCards = [Card(value, suit) for value in range(2, 15) for suit in ('D', 'S', 'C', 'H')]
		shuffle(PackOfCards)
		TrumpCard = PackOfCards.pop()

		self.Attributes.Round['trumpsuit'] = TrumpCard.ActualSuit
		self.Attributes.Round['PackOfCards'] = PackOfCards
		self.Attributes.Round['TrumpCard'] = TrumpCard
		self.Triggers.Surfaces['TrumpCard'] += 1

	def TrickStart(self, TrickNumber, FirstPlayer):
		self.Attributes.Trick['TrickInProgress'] = True
		self.Attributes.Trick['TrickNumber'] = TrickNumber

		FirstPlayerIndex = FirstPlayer.playerindex
		self.Attributes.Trick['FirstPlayerIndex'] = FirstPlayerIndex

		self.CardPositions = (self.StartCardPositions[FirstPlayerIndex:]
		                      + self.StartCardPositions[:FirstPlayerIndex])
		return FirstPlayerIndex

	def TrickMiddle(self, FirstPlayerIndex):
		self.WaitForPlayers('TrickStart')

		for i in chain(range(FirstPlayerIndex, self.Attributes.Tournament['PlayerNumber']), range(FirstPlayerIndex)):

			currentnumber = len(self.Attributes.Trick['PlayedCards'])
			self.Attributes.Trick['WhoseTurnPlayerIndex'] = i
			self.Triggers.Surfaces['CurrentBoard'] += 1

			while len(self.Attributes.Trick['PlayedCards']) == currentnumber:
				delay(60)

	def TrickEnd(self, PlayedCards):
		self.Attributes.Trick['WhoseTurnPlayerIndex'] = -1
		self.Attributes.Trick['TrickInProgress'] = False
		self.Attributes.Trick['Winner'] = (
			max((card.DetermineWinValue(PlayedCards[0].ActualSuit, self.Attributes.Round['trumpsuit'])
			     for card in PlayedCards), key=Card.GetWinValue)).PlayedBy

		self.Attributes.Trick['Winner'].WinsTrick()
		self.Attributes.Trick['FirstPlayerIndex'] = 0

		delay(500)

		PlayedCards.clear()
		self.Triggers.Surfaces['CurrentBoard'] += 1

		self.WaitForPlayers('TrickEnd')
		return self.Attributes.Trick['Winner']

	def NewGameReset(self):
		self.Attributes.Game['StartCardNumber'] = 0
		self.Attributes.Round['RoundNumber'] = 1

		Player.AllPlayers = Player.AllPlayers[1:] + Player.AllPlayers[:1]
		Player.AllPlayers = [player.ResetPlayer(Player.AllPlayers.index(player)) for player in Player.AllPlayers]

		self.Attributes.Tournament['gameplayers'] = Player.AllPlayers
		self.Attributes.Tournament['GamesPlayed'] += 1
		self.Triggers.Surfaces['Scoreboard'] += 1
		self.StartPlay = False
