from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from collections import UserList
from src.players.sort_hand import SortHand
from src.cards.suit import Suit

if TYPE_CHECKING:
	from src.players.players_abstract import Player
	from src.special_knock_types import CardList, IndexOrKey, SuitTuple
	from src.cards.server_card import ServerCard as Card


class Hand(UserList):
	__slots__ = 'Iteration', 'player'

	def __init__(self, player: Player):
		super().__init__()
		self.Iteration = 0
		self.player = player

	# noinspection PyAttributeOutsideInit
	def NewHand(self,
	            cards: CardList,
	            TrumpSuit: Suit):

		self.data = cards
		if cards:
			self.sort(TrumpSuit)
			self.data = [card.AddToHand(self.player.name) for card in self.data]

	def RemoveCard(
			self,
			card: Card,
			TrumpSuit: Suit
	):

		suitTuple = (self.data[0].Suit, self.data[-1].Suit)
		self.data.remove(card)
		self.sort(TrumpSuit, PlayedSuit=card.Suit, suit_tuple=suitTuple)

	def sort(
			self,
			TrumpSuit: Suit,
			PlayedSuit: Optional[Suit] = None,
			suit_tuple: SuitTuple = (None, None)
	):
		self.data = SortHand(self.data, TrumpSuit, PlayedSuit=PlayedSuit, SuitTuple=SuitTuple)

	def __getitem__(self, item: IndexOrKey):
		try:
			return super().__getitem__(item)
		except:
			return next(card for card in self.data if repr(card) == item)

	def __iter__(self):
		return iter(self.data)
