from __future__ import annotations

from traceback_with_variables import printing_exc
from random import shuffle
from typing import TYPE_CHECKING

from src.game.abstract_game import Game, EventsDict
from src.players.players_server import ServerPlayer as Player
from src.cards.server_card_suit_rank import ServerCard as Card

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import NumberInput, ServerCardList


DEFAULT_NETWORK_MESSAGE = 'pong'
KILL_PROGRAMME_MESSAGE = 'Terminate'


class ServerGame(Game):
	__slots__ = 'Operations', 'PlayerNumber'

	def __init__(
			self,
			BiddingSystem: str,
			PlayerNumber: int
	):
		super().__init__(BiddingSystem)

		# The PlayerNumber is set as an instance variable on the server side but a class variable on the client side.
		self.PlayerNumber = PlayerNumber
		self.Triggers = EventsDict()

		Player.MakePlayers(PlayerNumber)
		Card.MakePack()

		self.Operations = {
			# if the client is sending the name of that player
			'@P': lambda Info: self.AddPlayerName(Info),

			# if the client is telling us how many cards the game should start with
			'@N': lambda Info: self.SetCardNumber(Info),

			# if the client is trying to play a card
			'@C': lambda Info: self.ExecutePlay(Info[2:4], int(Info[4])),

			# if the client is telling us the players are ready to start the game
			'@S': lambda Info: self.TimeToStart(),

			# if the client is telling us how many tricks they are going to bid in this round.
			'@B': lambda Info: self.PlayerMakesBid(Info),

			# If the client is telling us whether they want an instant rematch after the game has ended.
			'@1': lambda Info: self.RepeatQuestionAnswer(),

			# If the client is saying they don't want a repeat game.
			'@T': lambda Info: KILL_PROGRAMME_MESSAGE,

			# If the client is telling us they've completed an animation sequence.
			'@A': lambda Info: self.PlayerActionCompleted(Info),

			# If it's just a ping to keep the connection going
			'pi': lambda Info: DEFAULT_NETWORK_MESSAGE
		}

	@staticmethod
	def AddPlayerName(Info):
		Player.AddName(Info[2:-1], int(Info[-1]))

	def SetCardNumber(self, number: NumberInput):
		self.StartCardNumber = int(number)

	def TimeToStart(self):
		self.StartPlay = True

	@staticmethod
	def PlayerActionCompleted(Info: str):
		Player.PlayerActionCompleted(int(Info[2]))

	@staticmethod
	def PlayerMakesBid(Info: str):
		Player.PlayerMakesBid(int(Info[4]), int(Info[2:4]))

	def RepeatQuestionAnswer(self):
		self.RepeatGame = True

	def WaitForPlayers(self, attribute: str):
		self.Triggers.Events[attribute] += 1
		Player.WaitForPlayers()

	def PlayGame(self):
		# Wait until the opening sequence is complete

		while not self.StartCardNumber:
			delay(1)

		Player.NextStage()

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
		Pack = Card.AllCardsList.copy()
		shuffle(Pack)
		self.TrumpCard = ((TrumpCard := Pack.pop()),)
		self.trumpsuit = (trumpsuit := TrumpCard.Suit)
		self.Triggers.Events['NewPack'] += 1

		# Deal cards
		Player.NewPack(Pack, cardnumber, trumpsuit)
		self.WaitForPlayers('CardsDealt')

		# Play tricks
		for i in range(cardnumber):
			self.PlayTrick()

		# Reset players for the next round.
		Player.EndOfRound()
		self.RoundCleanUp()

	def PlayTrick(self):
		self.WaitForPlayers('TrickStart')

		for i in range(self.PlayerNumber):
			while len(self.PlayedCards) == i:
				delay(100)

		Player.NextStage()
		self.WaitForPlayers('TrickWinnerLogged')
		self.PlayedCards.clear()
		self.WaitForPlayers('TrickEnd')

	def ClientCommsLoop(self):
		with printing_exc():
			while True:
				if Player.number() != self.PlayerNumber:
					raise Exception('A client appears to have left the game!')

				delay(300)
				self.Export()

	def Export(self):
		StartNo = self.StartCardNumber

		String = '---'.join((
			'--'.join([f'{v}' for v in self.Triggers.values()]),
			Player.ExportString(),
			CardsToString(self.PlayedCards),
			f'{int(self.StartPlay)}{int(self.RepeatGame)}{StartNo}{repr(self.TrumpCard) if self.TrumpCard else ""}'
		))

		for player in Player.iter():
			player.ScheduleSend('---'.join((String, CardsToString(player.Hand))))

	# PlayerNumber is given in the abstract_game repr
	def __repr__(self):
		return '\n'.join((
			super().__repr__(),
			f'gameplayers = {Player.reprList()}\nTriggers: {self.Triggers}'
		))


def CardsToString(L: ServerCardList):
	if not L:
		return 'None'
	return '--'.join([f'{Card.AllCardsList.index(card)}-{card.PlayedBy}' for card in L])
