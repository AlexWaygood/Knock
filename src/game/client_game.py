from __future__ import annotations

from typing import List, TYPE_CHECKING
from threading import RLock
from logging import getLogger
from itertools import chain
from queue import Queue
from time import time

from traceback_with_variables import printing_exc

from src.misc import DictLike
from src.game.abstract_game import Game, EventsDict
from src.players.players_client import ClientPlayer as Player
from src.game.client_scoreboard_data import Scoreboard
from src.cards.server_card_suit_rank import AllCardValues
from src.cards.client_card import ClientCard as Card
from src.network.netw_client import Client

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import NumberInput
	from src.display.input_context import InputContext


log = getLogger(__name__)


class NewCardQueues:
	__slots__ = 'Hand', 'PlayedCards', 'TrumpCard'

	def __init__(self):
		self.Hand = Queue()
		self.PlayedCards = Queue()
		self.TrumpCard = Queue()


class DoubleTrigger:
	__slots__ = 'Client', 'Server'

	def __init__(self):
		self.Client = EventsDict()
		self.Server = EventsDict()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return True


class ClientGame(Game, DictLike):
	__slots__ = 'GamesPlayed', 'CardNumberThisRound', 'RoundNumber', 'TrickInProgress', 'TrickNumber', \
	            'WhoseTurnPlayerIndex', 'PlayerOrder', 'RoundLeaderIndex', 'MaxCardNumber', 'NewCardQueues', \
	            'FrozenState', 'Scoreboard', 'client', 'lock'

	# The PlayerNumber is set as an instance variable on the server side but a class variable on the client side.
	PlayerNumber = 0
	OnlyGame = None

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	def __new__(
			cls,
			PlayerNumber: int,
			FrozenState: bool
	):
		cls.OnlyGame = super(ClientGame, cls).__new__(cls)
		cls.PlayerNumber = PlayerNumber
		return cls.OnlyGame

	def __init__(
			self,
			PlayerNumber: int,
			FrozenState: bool
	):
		super().__init__()
		self.FrozenState = FrozenState
		self.lock = RLock()
		self.client = Client.OnlyClient
		self.Triggers = DoubleTrigger()
		self.gameplayers = Player.AllPlayers
		self.gameplayers.AddVars(self)
		self.Scoreboard = Scoreboard(self.gameplayers)
		self.GamesPlayed = 0
		self.CardNumberThisRound = -1
		self.RoundNumber = 1
		self.TrickInProgress = False
		self.TrickNumber = 0
		self.WhoseTurnPlayerIndex = -1
		self.PlayerOrder: List[int] = []
		self.RoundLeaderIndex = -1
		self.MaxCardNumber = 51 // PlayerNumber
		self.NewCardQueues = NewCardQueues()

		[Player(i) for i in range(PlayerNumber)]
		[Card(*value) for value in AllCardValues]

	def TimeToStart(self):
		self.StartPlay = True
		self.client.SendQueue.put('@S')

	@property
	def StartCardNumber(self):
		return self._StartCardNumber

	@StartCardNumber.setter
	def StartCardNumber(self, number: NumberInput):
		self._StartCardNumber = int(number)
		self.Scoreboard.SetUp(self._StartCardNumber)

	def AttributeWait(self, attr: str):
		with self.Triggers as s:
			while s.Server[attr] == s.Client[attr]:
				delay(100)

			with self:
				s.Client[attr] = s.Server[attr]

	def StartRound(
			self,
			cardnumber: int,
			RoundLeaderIndex: int,
			RoundNumber: int
	):
		self.CardNumberThisRound = cardnumber
		self.RoundLeaderIndex = RoundLeaderIndex
		self.RoundNumber = RoundNumber

	def StartTrick(
			self,
			TrickNumber: int,
			FirstPlayerIndex: int,
			player: Player
	):
		self.TrickInProgress = True
		self.TrickNumber = TrickNumber
		self.PlayerOrder = list(chain(range(FirstPlayerIndex, self.PlayerNumber), range(FirstPlayerIndex)))
		player.PosInTrick = self.PlayerOrder.index(player.playerindex)
		return self.PlayerOrder, player.PosInTrick

	def PlayTrick(
			self,
			context: InputContext,
			Pos: int
	):
		with context(GameUpdatesNeeded=True):
			for i, val in enumerate(self.PlayerOrder):
				self.WhoseTurnPlayerIndex = val
				context.TrickClickNeeded = (len(self.PlayedCards) == Pos)

				while len(self.PlayedCards) == i:
					delay(100)

	def ExecutePlay(
			self,
			cardID: str,
			playerindex: int
	):
		super().ExecutePlay(cardID, playerindex)
		self.client.SendQueue.put(f'@C{cardID}{playerindex}')

	def EndTrick(self):
		WinningCard = max(self.PlayedCards, key=lambda card: card.GetWinValue(self.PlayedCards[0].Suit, self.trumpsuit))
		(Winner := self.gameplayers[WinningCard.PlayedBy]).WinsTrick()

		if self.TrickNumber != self.CardNumberThisRound:
			self.WhoseTurnPlayerIndex = -1
			self.TrickInProgress = False

		return Winner

	def EndRound(self):
		self.WhoseTurnPlayerIndex = -1
		self.TrickInProgress = False
		self.gameplayers.RoundCleanUp(self.CardNumberThisRound, self.RoundNumber)
		self.Scoreboard.UpdateScores(self.RoundNumber, self.CardNumberThisRound)
		self.RoundCleanUp()

		if self.RoundNumber != self.StartCardNumber:
			self.RoundNumber += 1
			self.CardNumberThisRound -= 1
			self.TrickNumber = 1

	def NewGameReset(self):
		super().NewGameReset()
		self.gameplayers.NewGame()
		self.RoundNumber = 1

	def UpdateLoop(
			self,
			context: InputContext,
			player: Player
	):

		with printing_exc():
			while True:
				delay(100)

				if not self.client.ReceiveQueue.empty():
					gameInfo = self.client.ReceiveQueue.get()

					if not self.FrozenState:
						log.debug(f'Obtained new message from Client, {gameInfo}.')

					if gameInfo != 'pong':
						with self.lock:
							self.UpdateFromServer(gameInfo, player.playerindex)

						if not self.FrozenState:
							log.debug('Client-side game successfully updated.')

				if self.client.SendQueue.empty():
					if context.GameUpdatesNeeded:
						self.client.send('@G')
					elif self.client.LastUpdate < time() - 5:
						self.client.send('ping')
					continue

				self.client.send(self.client.SendQueue.get())

	def __enter__(self):
		self.lock.acquire()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.lock.release()
		return True

	def __repr__(self):
		String = super().__repr__()
		Added = f'''gameplayers = {self.gameplayers}
GamesPlayed = {self.GamesPlayed}
CardNumberThisRound = {self.CardNumberThisRound}
RoundNumber = {self.RoundNumber}
TrickInProgress = {self.TrickInProgress}
TrickNumber = {self.TrickNumber}
WhoseTurnPlayerIndex = {self.WhoseTurnPlayerIndex}
PlayerOrder = {self.PlayerOrder}
RoundLeaderIndex = {self.RoundLeaderIndex}
MaxCardNumber = {self.MaxCardNumber}

'''
		return '\n'.join((String, Added))

	def UpdateFromServer(
			self,
			String: str,
			playerindex: int
	):

		StringList = String.split('---')

		for key, value in zip(self.Triggers.Server.keys(), StringList[0].split('--')):
			self.Triggers.Server[key] = int(value)

		PlayerInfoList = StringList[1].split('--')

		if any(isinstance(player.name, int) for player in self.gameplayers):
			for player, playerinfo in zip(self.gameplayers, PlayerInfoList):
				player.name = playerinfo.split('-')[0]
		else:
			for info in PlayerInfoList:
				name, bid = info.split('-')
				player = self.gameplayers[name]

				if bid == '*1':
					player.Bid = -1
				else:
					player.Bid = int(bid)

		if (Hand := StringList[2]) != 'None' and not self.gameplayers[playerindex].Hand:
			self.gameplayers[playerindex].Hand.NewHand(CardsFromString(Hand))
			self.NewCardQueues.Hand.put(1)

		if (PlayedCards := StringList[3]) != 'None':
			self.PlayedCards = CardsFromString(PlayedCards)
			self.NewCardQueues.PlayedCards.put(1)

		FinalString = StringList[4]
		self.StartPlay, self.RepeatGame = [bool(int(FinalString[i])) for i in range(2)]
		self.StartCardNumber = int(FinalString[2])

		if not self.TrumpCard:
			try:
				self.TrumpCard = (Card(AttemptToInt(FinalString[3]), FinalString[4]),)
				self.trumpsuit = self.TrumpCard[0].Suit
				self.NewCardQueues.TrumpCard.put(1)
			except KeyError:
				pass


def AttemptToInt(string: str):
	try:
		return int(string)
	except ValueError:
		return string


def CardsFromString(L: str):
	cards = [s.split('-') for s in L.split('--')]
	cards = [AllCardValues[int[c[0]]] for c in cards]
	return [Card(*c) for c in cards]
