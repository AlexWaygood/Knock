from __future__ import annotations

from typing import TYPE_CHECKING
from queue import Queue, Empty
from src.players.players_abstract import Player, Gameplayers
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import CardList, ConnectionAddress
	from src.cards.server_card_suit_rank import Suit


class SendQ:
	__slots__ = 'Q', 'LastUpdate'

	def __init__(self):
		self.Q = Queue(maxsize=1)
		self.LastUpdate = ''

	def put(self, data):
		if data != self.LastUpdate:
			self.Q.put(data)

	def get(self):
		self.LastUpdate = self.Q.get(block=False)
		return self.LastUpdate

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return exc_type is Empty


class ServerPlayer(Player):
	__slots__ = 'SendQ', 'addr', 'LastUpdate', 'ActionComplete'

	AllPlayers: Gameplayers[ServerPlayer]

	def __init__(self, playerindex):
		super().__init__(playerindex)
		self.SendQ = SendQ()
		self.addr: ConnectionAddress = tuple()
		self.ActionComplete = False

	@classmethod
	def NewPack(
			cls,
			Pack: CardList,
			CardNo: int,
			trumpsuit: Suit
	):
		for player in cls.AllPlayers:
			player.ReceiveCards([Pack.pop() for _ in range(CardNo)], trumpsuit)

	@classmethod
	def AddName(
			cls,
			name: str,
			playerindex: int
	):
		cls.AllPlayers[playerindex].name = name
		return all(isinstance(player.name, str) for player in cls.AllPlayers)

	@classmethod
	def NextStage(cls):
		for player in cls.AllPlayers:
			player.ActionComplete = False

	@classmethod
	def PlayerMakesBid(
			cls,
			index: int,
			Bid: int
	):
		cls.AllPlayers[index].Bid = Bid

	@classmethod
	def PlayerActionCompleted(cls, index: int):
		cls.AllPlayers[index].ActionComplete = True

	@classmethod
	def WaitForPlayers(cls):
		while any(not player.ActionComplete for player in cls.AllPlayers):
			delay(1)

		ServerPlayer.NextStage()

	@classmethod
	def EndOfRound(cls):
		for player in cls.AllPlayers:
			player.Bid = -1

	@classmethod
	def ExportString(cls):
		return '--'.join(f'{player.name}-{B if (B := player.Bid) > -1 else "*1"}' for player in cls.AllPlayers)

	def ReprInfo(self):
		return '\n'.join((
			super().ReprInfo(),
			f'addr: {self.addr}. ActionComplete: {self.ActionComplete}.'
		))

	def MakeBid(self, number: int):
		self.Bid = number
		self.ActionComplete = True
		return self

	def ScheduleSend(self, GameString):
		self.SendQ.put(GameString)
