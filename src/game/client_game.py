from __future__ import annotations

from itertools import chain
from queue import Queue
from traceback_with_variables import printing_exc
from time import time
from typing import List, TYPE_CHECKING, Dict

from src.data_structures import DictLike
from src.game.abstract_game import Game
from src.players.players_client import ClientPlayer as Player
from src.cards.client_card import AllCardValues, ClientCard as Card
from src.network.server_updaters import DoubleTrigger

from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import NumberInput
	from src.display.input_context import InputContext
	from src.network.client_class import Client


class NewCardQueues:
	__slots__ = 'Hand', 'PlayedCards', 'TrumpCard'

	def __init__(self):
		self.Hand = Queue()
		self.PlayedCards = Queue()
		self.TrumpCard = Queue()


class ClientGame(Game, DictLike):
	__slots__ = 'GamesPlayed', 'CardNumberThisRound', 'RoundNumber', 'TrickInProgress', 'TrickNumber', \
	            'WhoseTurnPlayerIndex', 'PlayerOrder', 'RoundLeaderIndex', 'MaxCardNumber', 'NewCardQueues'

	def __init__(self, PlayerNumber: int):
		super().__init__(PlayerNumber)
		self.Triggers = DoubleTrigger()
		self.gameplayers = Player.AllPlayers
		self.gameplayers.PlayerNo = PlayerNumber
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

	@property
	def StartCardNumber(self):
		return self._StartCardNumber

	@StartCardNumber.setter
	def StartCardNumber(self, number: NumberInput):
		self._StartCardNumber = int(number)
		self.gameplayers.InitialiseScoreboard(self)

	def AttributeWait(self, attr: str):
		with self.Triggers as s:
			while s.Server.Events[attr] == s.Client.Events[attr]:
				delay(100)

			with self:
				s.Client.Events[attr] = s.Server.Events[attr]

	def StartRound(self,
	               cardnumber: int,
	               RoundLeaderIndex: int,
	               RoundNumber: int):

		self.CardNumberThisRound = cardnumber
		self.RoundLeaderIndex = RoundLeaderIndex
		self.RoundNumber = RoundNumber

	def StartTrick(self,
	               TrickNumber: int,
	               FirstPlayerIndex: int,
	               player: Player):

		self.TrickInProgress = True
		self.TrickNumber = TrickNumber
		self.PlayerOrder = list(chain(range(FirstPlayerIndex, self.PlayerNumber), range(FirstPlayerIndex)))
		player.PosInTrick = self.PlayerOrder.index(player.playerindex)
		return self.PlayerOrder, player.PosInTrick

	def PlayTrick(self,
	              context: InputContext,
	              Pos: int):

		with context(GameUpdatesNeeded=True):
			for i, val in enumerate(self.PlayerOrder):
				self.WhoseTurnPlayerIndex = val

				while (CardsOnBoard := len(self.PlayedCards)) == i:
					delay(100)
					context.TrickClickNeeded = (CardsOnBoard == Pos)

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
			client: Client,
			player: Player
	):

		with printing_exc():
			while True:
				delay(100)

				if not client.ReceiveQueue.empty():
					gameInfo = client.ReceiveQueue.get()
					if gameInfo != 'pong':
						with self.lock:
							self.UpdateFromServer(gameInfo, player.playerindex)

				if client.SendQueue.empty():
					if context.GameUpdatesNeeded:
						client.ClientSend('@G')
					elif client.LastUpdate < time() - 5:
						client.ClientSend('ping')
					continue

				client.ClientSend(client.SendQueue.get())

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

		for i, attr in enumerate(('Events', 'Surfaces')):
			UpdateDictFromString(self.Triggers.Server[attr], StringList[i])

		PlayerInfoList = StringList[2].split('--')

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

		if (Hand := StringList[3]) != 'None' and not self.gameplayers[playerindex].Hand:
			self.gameplayers[playerindex].ReceiveCards(CardsFromString(Hand))
			self.NewCardQueues.Hand.put(1)

		if (PlayedCards := StringList[4]) != 'None':
			self.PlayedCards = CardsFromString(PlayedCards)
			self.NewCardQueues.PlayedCards.put(1)

		FinalString = StringList[6]
		self.StartPlay, self.RepeatGame = [bool(int(FinalString[i])) for i in range(2)]
		self.StartCardNumber = int(FinalString[2])

		if not self.TrumpCard:
			try:
				# noinspection PyTypeChecker
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
	cards = [[AttemptToInt(c[0][0]), c[0][1], c[1]] for c in cards]
	return [Card(*c) for c in cards]


def UpdateDictFromString(D: Dict[str: int], String: str):
	for key, value in zip(D.keys(), String.split('--')):
		D[key] = int(value)
