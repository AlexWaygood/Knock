from __future__ import annotations
from typing import TYPE_CHECKING
from functools import lru_cache
from src.display.abstract_surfaces.knock_surface_with_cards import KnockSurfaceWithCards
from src.display.faders import OpacityFader
from src.global_constants import HAND_CARD_FADE_KEY, OPAQUE_OPACITY_KEY

if TYPE_CHECKING:
	from src.special_knock_types import PositionSequence
	from src.cards.client_card import ClientCard as Card


HAND_SURFACE_X_COORDINATE = 0  # The Hand surface's Y-coordinate changes, but the X-coordinate never does
COVER_RECT_START_OPACITY = OPAQUE_OPACITY_KEY


@lru_cache
def GetHandRects(
		GameSurfX: int,
		WindowMargin: int,
		CardX: int,
		StartNumber: int
) -> PositionSequence:

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

	x = HAND_SURFACE_X_COORDINATE

	def __init__(self) -> None:
		self.CardList = self.player.Hand
		self.CardFadeManager = OpacityFader(COVER_RECT_START_OPACITY, HAND_CARD_FADE_KEY)
		self.CardUpdateQueue = self.game.NewCardQueues.Hand
		super().__init__()   # calls SurfDimensions()
		self.HandRectsCalculated = False

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self) -> None:
		self.y = self.GameSurf.Height - (self.CardY + self.WindowMargin)
		self.Width = self.GameSurf.Width
		self.Height = self.CardY + self.WindowMargin

	def GetHandRects(self) -> None:
		self.AddRectList(GetHandRects(self.Width, self.WindowMargin, self.CardX, self.game.StartCardNumber))
		self.HandRectsCalculated = True

	def ClearRectList(self) -> None:
		self.RectList.clear()
		self.CoverRects.clear()
		self.HandRectsCalculated = False

	def UpdateCard(self, card: Card, index: int) -> None:
		card.ReceiveRect(self.RectList[index], self.attrs.topleft, self.GameSurf.attrs.topleft, CardInHand=True)

	# Update, GetSurfBlits & Initialise methods not defined here as the base class doesn't need to be overridden.
