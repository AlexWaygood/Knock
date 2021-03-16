from __future__ import annotations

from random import shuffle
from typing import TYPE_CHECKING

from src.game.abstract_game import Game
from src.network.server_updaters import Triggers
from src.players.players_server import ServerPlayer as Player
from src.cards.server_card import ServerCard as Card

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import CardList, NumberInput, UpdaterDict


class ServerGame(Game):
	__slots__ = 'Operations', 'PlayerNumber'

	def __init__(self, PlayerNumber: int):
		super().__init__()
		self.PlayerNumber = PlayerNumber
		self.gameplayers = Player.AllPlayers
		self.gameplayers.PlayerNo = PlayerNumber
		self.Triggers = Triggers()

		[Player(i) for i in range(PlayerNumber)]

		self.Operations = {
			# if the client is just asking for an updated copy of the game
			'@G': lambda Info: None,

			# if the client is sending the name of that player
			'@P': lambda Info: self.AddPlayerName(Info[2:4], int(Info[-1])),

			# if the client is telling us how many cards the game should start with
			'@N': lambda Info: self.SetCardNumber(Info),

			# if the client is trying to play a card
			'@C': lambda Info: self.ExecutePlay(Info[2:4], int(Info[4])),

			# if the client is telling us the players are ready to start the game
			'@S': lambda Info: self.TimeToStart(),

			# if the client is telling us how many tricks they are going to bid in this round.
			'@B': lambda Info: self.PlayerMakesBid(int(Info[2:4]), int(Info[4])),

			# If the client is telling us whether they want an instant rematch after the game has ended.
			'@1': lambda Info: self.RepeatQuestionAnswer(),

			# If the client is saying they don't want a repeat game.
			'@T': lambda Info: 'Terminate',

			# If the client is telling us they've completed an animation sequence.
			'@A': lambda Info: self.PlayerActionCompleted(int(Info[2])),

			# If it's just a ping to keep the connection going
			'pi': lambda Info: 'pong'
		}

	def SetCardNumber(self, number: NumberInput):
		self.StartCardNumber = int(number)

	def TimeToStart(self):
		self.StartPlay = True

	def PlayerActionCompleted(self, playerindex: int):
		self.gameplayers[playerindex].ActionComplete = True

	def RepeatQuestionAnswer(self):
		self.RepeatGame = True

	def WaitForPlayers(self, attribute: str):
		self.Triggers.Events[attribute] += 1
		self.gameplayers.WaitForPlayers()

	def PlayGame(self):
		# Wait until the opening sequence is complete

		while not self.StartCardNumber:
			delay(1)

		self.gameplayers.NextStage()
		self.WaitForPlayers('GameInitialisation')
		self.Triggers.Events['StartNumberSet'] += 1

		for cardnumber in range(self.StartCardNumber, 0, -1):
			self.PlayRound(cardnumber)

		self.RepeatGame = False

		while not self.RepeatGame:
			delay(1)

		self.NewGameReset()

		# Wait until all players have logged their new playerindex.
		self.WaitForPlayers('NewGameReset')

	def PlayRound(self, cardnumber: int):
		# Make a new pack of cards, set the trumpsuit.
		Pack = Card.AllCards.copy()
		shuffle(Pack)
		with self.lock:
			self.TrumpCard = ((TrumpCard := Pack.pop()),)
			self.trumpsuit = (trumpsuit := TrumpCard.Suit)
			self.Triggers.Events['NewPack'] += 1

		# Deal cards
		with self.lock:
			self.gameplayers.ReceiveCards(Pack, cardnumber, trumpsuit)
			self.IncrementTriggers('TrumpCard', 'Board', 'Scoreboard')
		self.WaitForPlayers('CardsDealt')

		# Play tricks
		for i in range(cardnumber):
			self.PlayTrick()

		# Reset players for the next round.
		with self.lock:
			self.gameplayers.RoundCleanUp()
			self.RoundCleanUp()

	def PlayTrick(self):
		self.WaitForPlayers('TrickStart')

		for i in range(self.PlayerNumber):
			self.IncrementTriggers('Board')
			while len(self.PlayedCards) == i:
				delay(100)

		self.gameplayers.NextStage()
		self.WaitForPlayers('TrickWinnerLogged')
		self.PlayedCards.clear()
		self.IncrementTriggers('Board')
		self.WaitForPlayers('TrickEnd')

	def Export(self, playerindex: int):
		EventsString = DictToString(self.Triggers.Events)
		SurfaceTriggerString = DictToString(self.Triggers.Surfaces)

		PlayerString = '--'.join(
			f'{player.name}-{B if (B := player.Bid) > -1 else "*1"}' for player in self.gameplayers
		)

		PlayerHandString = CardsToString(self.gameplayers[playerindex].Hand)
		CardsOnBoardString = CardsToString(self.PlayedCards)
		TournamentStatus = f'{int(self.StartPlay)}{int(self.RepeatGame)}{self.StartCardNumber}' \
		                   f'{repr(self.TrumpCard) if self.TrumpCard else ""}'

		return '---'.join((
			EventsString,
			SurfaceTriggerString,
			PlayerString,
			PlayerHandString,
			CardsOnBoardString,
			TournamentStatus
		))


def DictToString(D: UpdaterDict):
	return '--'.join(f'{v}' for v in D.values())


def CardsToString(L: CardList):
	if not L:
		return 'None'
	return '--'.join([f'{card!r}-{card.PlayedBy}' for card in L])
