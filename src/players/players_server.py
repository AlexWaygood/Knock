from __future__ import annotations

from typing import TYPE_CHECKING
from queue import Queue, Empty
from src.players.players_abstract import Player, Hand
# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import delay

if TYPE_CHECKING:
	import src.special_knock_types as skt
	from src.cards.server_card_suit_rank import Suit


class SendQ:
	__slots__ = 'Q', 'LastUpdate'

	def __init__(self) -> None:
		self.Q = Queue(maxsize=1)
		self.LastUpdate = ''

	def put(self, data: str) -> None:
		if data != self.LastUpdate:
			if self.Q.full():
				self.Q.get()
			self.Q.put(data)

	def get(self) -> str:
		self.LastUpdate = self.Q.get(block=False)
		return self.LastUpdate

	def empty(self) -> bool:
		return self.Q.empty()

	def __enter__(self) -> SendQ:
		return self

	def __exit__(
			self,
			exc_type: skt.ExitArg1,
			exc_val: skt.ExitArg2,
			exc_tb: skt.ExitArg3
	) -> bool:

		return exc_type is Empty


class ServerPlayer(Player):
	__slots__ = 'SendQ', 'addr', 'LastUpdate', 'ActionComplete'

	_AllPlayers: skt.ServerPlayerList
	_AllPlayersDict: skt.ServerPlayerDict

	def __init__(self, playerindex: int) -> None:
		super().__init__(playerindex)
		self.SendQ = SendQ()
		self.addr: skt.ConnectionAddress = tuple()
		self.ActionComplete = False
		self.Hand = Hand()

	@classmethod
	def NewPack(
			cls,
			Pack: skt.ServerCardList,
			CardNo: int,
			trumpsuit: Suit
	) -> None:

		[player.ReceiveCards([Pack.pop() for _ in range(CardNo)], trumpsuit) for player in cls.iter()]

	@classmethod
	def AddName(
			cls,
			name: str,
			playerindex: int
	) -> bool:

		cls.player(playerindex).name = name
		return all(isinstance(player.name, str) for player in cls.iter())

	@classmethod
	def NextStage(cls) -> None:
		for player in cls.iter():
			player.ActionComplete = False

	@classmethod
	def PlayerMakesBid(
			cls,
			index: int,
			Bid: int
	) -> None:

		cls.player(index).Bid = Bid

	@classmethod
	def PlayerActionCompleted(cls, index: int) -> None:
		cls.player(index).ActionComplete = True

	@classmethod
	def WaitForPlayers(cls) -> None:
		while any(not player.ActionComplete for player in cls.iter()):
			delay(1)

		ServerPlayer.NextStage()

	@classmethod
	def EndOfRound(cls) -> None:
		for player in cls.iter():
			player.Bid = -1

	@classmethod
	def ExportString(cls) -> str:
		return '--'.join(f'{player.name}-{B if (B := player.Bid) > -1 else "*1"}' for player in cls.iter())

	def connect(
			self,
			addr: skt.ConnectionAddress,
			gameInfo: str
	) -> ServerPlayer:

		self.addr = addr
		self.SendQ.put(gameInfo)
		return self

	def ReprInfo(self) -> str:
		return '\n'.join((
			super().__repr__(),
			f'addr: {self.addr}. ActionComplete: {self.ActionComplete}.'
		))

	def MakeBid(self, number: int) -> ServerPlayer:
		self.Bid = number
		self.ActionComplete = True
		return self

	def ScheduleSend(self, GameString: str) -> None:
		self.SendQ.put(GameString)

	def NothingToSend(self) -> bool:
		return self.SendQ.empty()
