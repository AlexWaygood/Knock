from __future__ import annotations
from functools import lru_cache
from typing import TYPE_CHECKING

from src.display.abstract_surfaces.knock_surface_with_cards import KnockSurfaceWithCards
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.faders import OpacityFader

if TYPE_CHECKING:
	from src.cards.client_card import ClientCard as Card


START_COVER_RECT_OPACITY = 'OpaqueOpacity'
FONT = 'TrumpCardFont'
TRUMPCARD_SURFACE_TITLE = 'TrumpCard'


@lru_cache
def TrumpCardDimensionsHelper(
		GameX: int,
		CardX: int,
		CardY: int,
		NormalLinesize: int
):
	return (GameX - (CardX + 50)), (CardX + 2), (CardY + int(NormalLinesize * 2.5) + 10), (1, int(NormalLinesize * 2.5))


# noinspection PyAttributeOutsideInit
class TrumpCardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	__slots__ = 'font'

	def __init__(self):
		self.CardList = self.game.TrumpCard
		self.CardFadeManager = OpacityFader(START_COVER_RECT_OPACITY, 'TrumpCard')
		self.CardUpdateQueue = self.game.NewCardQueues.TrumpCard
		super().__init__()   # Calls SurfDimensions()

	def Initialise(self):
		self.font = self.Fonts[FONT]
		return super().Initialise()

	def SurfDimensions(self):
		Vals = TrumpCardDimensionsHelper(self.GameSurf.Width, self.CardX, self.CardY, self.font.linesize)
		self.x, self.Width, self.Height, TrumpCardPos = Vals
		self.y = self.WindowMargin
		self.AddRectList((TrumpCardPos,))

	def UpdateCard(
			self,
			card: Card,
			index: int
	):
		card.ReceiveRect(self.RectList[0])

	def GetSurfBlits(self):
		L = super().GetSurfBlits()
		font, LineSize = self.font, self.font.linesize
		return L + [self.GetText(TRUMPCARD_SURFACE_TITLE, font, center=((self.attrs.centre[0] / 2), (LineSize / 2)))]
