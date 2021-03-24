from __future__ import annotations

from os import environ, path
from typing import TYPE_CHECKING
from functools import lru_cache
from PIL import Image

from src.cards.server_card_suit_rank import Suit, AllCardIDs, ServerCard

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.transform import rotozoom
from pygame.image import fromstring as pg_image_fromstring

if TYPE_CHECKING:
	from fractions import Fraction
	from pygame import Rect
	from src.special_knock_types import RankType, Position, CardImageDict, TupledImageDict, OptionalSurface, OptionalRect


def OpenImage(
		ID: str,
		ResizeRatio: Fraction
):
	im = Image.open(path.join(ClientCard.PathToImages, f'{ID}.jpg')).convert("RGB")
	im = im.resize((int(im.size[0] / ResizeRatio), int(im.size[1] / ResizeRatio)))
	return pg_image_fromstring(im.tobytes(), im.size, im.mode).convert()


@lru_cache
def CardResizer(
		ResizeRatio: Fraction,
		BaseCardImages: TupledImageDict
):
	return {ID: rotozoom(cardimage, 0, (1 / ResizeRatio)) for ID, cardimage in BaseCardImages}


class ClientCard(ServerCard):
	__slots__ = 'rect', 'colliderect', 'image', 'surfandpos'

	BaseCardImages: CardImageDict = {}
	CardImages: CardImageDict = {}
	OriginalImageDimensions = (691, 1056)  # Used in the SurfaceCoordinator script
	PathToImages = path.join('Images', 'Cards', 'Compressed')

	def __init__(
			self,
			rank: RankType,
			suit: str
	):

		super().__init__(rank, suit)
		self.rect: OptionalRect = None
		self.colliderect = self.rect
		self.image: OptionalSurface = None
		self.surfandpos = tuple()

	def ReceiveRect(
			self,
			rect: Rect,
			SurfPos: Position = None,
			GameSurfPos: Position = None,
			CardInHand: bool = False
	):

		self.rect = rect
		self.surfandpos = (self.image, self.rect)

		if CardInHand:
			self.colliderect = rect.move(*SurfPos).move(*GameSurfPos)

	def GetWinValue(
			self,
			playedsuit: Suit,
			trumpsuit: Suit
	):

		if self.Suit == playedsuit:
			return self.Rank.Value
		return self.Rank.Value + 13 if self.Suit == trumpsuit else 0

	def MoveColliderect(self, XMotion, YMotion):
		self.colliderect.move_ip(XMotion, YMotion)

	@classmethod
	def UpdateAtrributes(cls):
		for card in cls.AllCardsList:
			card.image = cls.CardImages[repr(card)]
			card.surfandpos = (card.image, card.rect)

	@classmethod
	def AddImages(cls, RequiredResizeRatio: Fraction):
		cls.BaseCardImages = {ID: OpenImage(ID, RequiredResizeRatio) for ID in AllCardIDs}
		cls.CardImages = cls.BaseCardImages.copy()
		cls.UpdateAtrributes()

	# noinspection PyTypeChecker
	@classmethod
	def UpdateImages(cls, ResizeRatio: Fraction):
		cls.CardImages = CardResizer(ResizeRatio, tuple(cls.BaseCardImages.items()))
		cls.UpdateAtrributes()
