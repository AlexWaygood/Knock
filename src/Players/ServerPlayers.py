from typing import Union
from src.Players.AbstractPlayers import Gameplayers, Player
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


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

	def ReceiveCards(self, Pack, CardNo, trumpsuit):
		"""
		@type Pack: list[src.Cards.ServerCard.ServerCard]
		@type CardNo: int
		@type trumpsuit: src.Cards.Suit.Suit
		"""

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

	def MakeBid(self, number: Union[int, str]):
		self.Bid = int(number)
		self.ActionComplete = True
		return self
