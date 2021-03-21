from __future__ import annotations
from typing import TYPE_CHECKING
from functools import lru_cache
from src.display.abstract_surfaces.knock_surface_with_cards import KnockSurfaceWithCards
from src.display.faders import OpacityFader

if TYPE_CHECKING:
	from src.cards.client_card import ClientCard as Card


@lru_cache
def GetHandRects(GameSurfX: int,
                 WindowMargin: int,
                 CardX: int,
                 StartNumber: int):

	x = WindowMargin
	DoubleWindowMargin = x * 2
	PotentialBuffer = CardX // 2

	if ((CardX * StartNumber) + DoubleWindowMargin + (PotentialBuffer * (StartNumber - 1))) < GameSurfX:
		CardBufferInHand = PotentialBuffer
	else:
		CardBufferInHand = min(x, ((GameSurfX - DoubleWindowMargin - (CardX * StartNumber)) // (StartNumber - 1)))

	return [((x + (i * (CardX + CardBufferInHand))), 0) for i in range(StartNumber)]


class HandSurface(KnockSurfaceWithCards):
	__slots__ = 'HandRectsCalculated'
	x = 0

	def __init__(self):
		self.CardList = self.player.Hand
		self.CardFadeManager = OpacityFader('OpaqueOpacity', 'Hand')
		self.CardUpdateQueue = self.game.NewCardQueues.Hand
		super().__init__()   # calls SurfDimensions()
		self.HandRectsCalculated = False

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self):
		self.y = self.GameSurf.Height - (self.CardY + self.WindowMargin)
		self.Width = self.GameSurf.Width
		self.Height = self.CardY + self.WindowMargin

	def GetHandRects(self):
		self.AddRectList(GetHandRects(self.Width, self.WindowMargin, self.CardX, self.game.StartCardNumber))
		self.HandRectsCalculated = True

	def ClearRectList(self):
		self.RectList.clear()
		self.CoverRects.clear()
		self.HandRectsCalculated = False

	def UpdateCard(
			self,
			card: Card,
			index: int
	):
		card.ReceiveRect(self.RectList[index], self.attrs.topleft, self.GameSurf.attrs.topleft, CardInHand=True)

	# Update, GetSurfBlits & Initialise methods not defined here as the base class doesn't need to be overridden.
