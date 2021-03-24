from __future__ import annotations

from typing import TYPE_CHECKING
from queue import Queue, Empty
from src.players.players_abstract import Player, Hand
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import ServerCardList, ConnectionAddress, ServerPlayerList, ServerPlayerDict
	from src.cards.server_card_suit_rank import Suit


class SendQ:
	__slots__ = 'Q', 'LastUpdate'

	def __init__(self):
		self.Q = Queue(maxsize=1)
		self.LastUpdate = ''

	def put(self, data):
		if data != self.LastUpdate:
			if self.Q.full():
				self.Q.get()
			self.Q.put(data)

	def get(self):
		self.LastUpdate = self.Q.get(block=False)
		return self.LastUpdate

	def empty(self):
		return self.Q.empty()

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return exc_type is Empty


class ServerPlayer(Player):
	__slots__ = 'SendQ', 'addr', 'LastUpdate', 'ActionComplete'

	_AllPlayers: ServerPlayerList
	_AllPlayersDict: ServerPlayerDict

	def __init__(self, playerindex):
		super().__init__(playerindex)
		self.SendQ = SendQ()
		self.addr: ConnectionAddress = tuple()
		self.ActionComplete = False
		self.Hand = Hand()

	@classmethod
	def NewPack(
			cls,
			Pack: ServerCardList,
			CardNo: int,
			trumpsuit: Suit
	):
		for player in cls.iter():
			player.ReceiveCards([Pack.pop() for _ in range(CardNo)], trumpsuit)

	@classmethod
	def AddName(
			cls,
			name: str,
			playerindex: int
	):
		cls.player(playerindex).name = name
		return all(isinstance(player.name, str) for player in cls.iter())

	@classmethod
	def NextStage(cls):
		for player in cls.iter():
			player.ActionComplete = False

	@classmethod
	def PlayerMakesBid(
			cls,
			index: int,
			Bid: int
	):
		cls.player(index).Bid = Bid

	@classmethod
	def PlayerActionCompleted(cls, index: int):
		cls.player(index).ActionComplete = True

	@classmethod
	def WaitForPlayers(cls):
		while any(not player.ActionComplete for player in cls.iter()):
			delay(1)

		ServerPlayer.NextStage()

	@classmethod
	def EndOfRound(cls):
		for player in cls.iter():
			player.Bid = -1

	@classmethod
	def ExportString(cls):
		return '--'.join(f'{player.name}-{B if (B := player.Bid) > -1 else "*1"}' for player in cls.iter())

	def connect(
			self,
			addr: ConnectionAddress,
			gameInfo: str
	):
		self.addr = addr
		self.SendQ.put(gameInfo)
		return self

	def ReprInfo(self):
		return '\n'.join((
			super().__repr__(),
			f'addr: {self.addr}. ActionComplete: {self.ActionComplete}.'
		))

	def MakeBid(self, number: int):
		self.Bid = number
		self.ActionComplete = True
		return self

	def ScheduleSend(self, GameString):
		self.SendQ.put(GameString)

	def NothingToSend(self):
		return self.SendQ.empty()
