from __future__ import annotations

from typing import List, TYPE_CHECKING
from threading import RLock
from itertools import chain
from queue import Queue
from operator import methodcaller

from src.misc import DictLike
from src.game.abstract_game import Game, EventsDict
from src.players.players_client import ClientPlayer as Player
from src.game.client_scoreboard_data import Scoreboard
from src.cards.server_card_suit_rank import AllCardValues
from src.cards.client_card import ClientCard as Card
from src.network.network_client import Client

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import NumberInput, OptionalClientGame
	from src.display.input_context import InputContext


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
	OnlyGame: OptionalClientGame = None

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
		Player.AddVars(self)
		self.Scoreboard = Scoreboard()
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
		self.client.QueueMessage('@S')

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
		self.client.QueueMessage(f'@C{cardID}{playerindex}')

	def EndTrick(self):
		WinningCard = max(self.PlayedCards, key=methodcaller('GetWinValue', self.PlayedCards[0].Suit, self.trumpsuit))
		(Winner := Player.AllPlayers[WinningCard.PlayedBy]).WinsTrick()

		if self.TrickNumber != self.CardNumberThisRound:
			self.WhoseTurnPlayerIndex = -1
			self.TrickInProgress = False

		return Winner

	def EndRound(self):
		self.WhoseTurnPlayerIndex = -1
		self.TrickInProgress = False
		Player.RoundCleanUp()
		self.Scoreboard.UpdateScores(self.RoundNumber, self.CardNumberThisRound)
		self.RoundCleanUp()

		if self.RoundNumber != self.StartCardNumber:
			self.RoundNumber += 1
			self.CardNumberThisRound -= 1
			self.TrickNumber = 1

	def NewGameReset(self):
		super().NewGameReset()
		Player.NewGame()
		self.RoundNumber = 1

	def __enter__(self):
		self.lock.acquire()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.lock.release()
		return True

	def __repr__(self):
		String = super().__repr__()
		Added = f'''gameplayers = {Player.AllPlayers}
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

		if not Player.AllPlayersHaveJoinedTheGame():
			for player, playerinfo in zip(Player.AllPlayers, PlayerInfoList):
				player.name = playerinfo.split('-')[0]
		else:
			for info in PlayerInfoList:
				name, bid = info.split('-')
				player = Player.AllPlayers[name]

				if bid == '*1':
					player.Bid = -1
				else:
					player.Bid = int(bid)

		if (PlayedCards := StringList[2]) != 'None':
			self.PlayedCards = CardsFromString(PlayedCards)
			self.NewCardQueues.PlayedCards.put(1)

		TournamentString = StringList[3]
		self.StartPlay, self.RepeatGame = [bool(int(TournamentString[i])) for i in range(2)]
		self.StartCardNumber = int(TournamentString[2])

		if not self.TrumpCard:
			try:
				self.TrumpCard = (Card(AttemptToInt(TournamentString[3]), TournamentString[4]),)
				self.trumpsuit = self.TrumpCard[0].Suit
				self.NewCardQueues.TrumpCard.put(1)
			except KeyError:
				pass

		if (Hand := StringList[4]) != 'None' and not Player.AllPlayers[playerindex].Hand:
			Player.AllPlayers[playerindex].Hand.NewHand(CardsFromString(Hand))
			self.NewCardQueues.Hand.put(1)


def AttemptToInt(string: str):
	try:
		return int(string)
	except ValueError:
		return string


def CardsFromString(L: str):
	cards = [s.split('-') for s in L.split('--')]
	cards = [AllCardValues[int[c[0]]] for c in cards]
	return [Card(*c) for c in cards]
