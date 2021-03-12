from __future__ import annotations

from typing import TYPE_CHECKING
from src.Players.AbstractPlayers import Gameplayers, Player
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.SpecialKnockTypes import CardList, NumberInput
	from src.Cards.Suit import Suit


class ServerGameplayers(Gameplayers):
	__slots__ = ()

	def NextStage(self):
		self.data = [player.NextStage() for player in self.data]

	def WaitForPlayers(self):
		while any(not player.ActionComplete for player in self.data):
			delay(1)

		self.NextStage()

	def RoundCleanUp(self):
		self.data = [player.EndOfRound() for player in self.data]

	def ReceiveCards(self,
	                 Pack: CardList,
	                 CardNo: int,
	                 trumpsuit: Suit):

		self.data = [player.ReceiveCards([Pack.pop() for _ in range(CardNo)], trumpsuit) for player in self.data]


class ServerPlayer(Player):
	AllPlayers = ServerGameplayers()

	def NextStage(self):
		self.ActionComplete = False
		return self

	def EndOfRound(self):
		self.Hand.Iteration += 1
		self.Bid = -1
		return self

	def MakeBid(self, number: NumberInput):
		self.Bid = int(number)
		self.ActionComplete = True
		return self
