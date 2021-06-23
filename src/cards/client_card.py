from __future__ import annotations

from os import path
from typing import TYPE_CHECKING
from functools import lru_cache
from PIL import Image
from src.cards.server_card_suit_rank import Suit, AllCardIDs, ServerCard

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.transform import rotozoom
from pygame.image import fromstring as pg_image_fromstring

if TYPE_CHECKING:
	from fractions import Fraction
	from pygame import Rect, Surface
	import src.special_knock_types as skt


PATH_TO_CARD_IMAGES = path.join('Images', 'Cards', 'Compressed')


def OpenImage(ID: str, ResizeRatio: Fraction) -> Surface:
	im = Image.open(path.join(PATH_TO_CARD_IMAGES, f'{ID}.jpg')).convert("RGB")
	im = im.resize((int(im.size[0] / ResizeRatio), int(im.size[1] / ResizeRatio)))
	return pg_image_fromstring(im.tobytes(), im.size, im.mode).convert()


@lru_cache
def CardResizer(ResizeRatio: Fraction, BaseCardImages: skt.TupledImageDict) -> skt.CardImageDict:
	return {ID: rotozoom(cardimage, 0, (1 / ResizeRatio)) for ID, cardimage in BaseCardImages}


class ClientCard(ServerCard):
	__slots__ = 'rect', 'colliderect', 'image', 'surfandpos'

	AllCardsList: skt.ClientCardList
	AllCardDict: skt.ClientCardDict

	BaseCardImages: skt.CardImageDict = {}
	CardImages: skt.CardImageDict = {}

	def __init__(
			self,
			rank: skt.RankType,
			suit: str
	) -> None:

		super().__init__(rank, suit)
		self.rect: skt.OptionalRect = None
		self.colliderect = self.rect
		self.image: skt.OptionalSurface = None
		self.surfandpos = tuple()

	def ReceiveRect(
			self,
			rect: Rect,
			SurfPos: skt.Position = None,
			GameSurfPos: skt.Position = None,
			CardInHand: bool = False
	) -> None:

		self.rect = rect
		self.surfandpos = (self.image, self.rect)

		if CardInHand:
			self.colliderect = rect.move(*SurfPos).move(*GameSurfPos)

	def GetWinValue(self, playedsuit: Suit, trumpsuit: Suit) -> int:
		if self.Suit == playedsuit:
			return self.Rank.Value
		return self.Rank.Value + 13 if self.Suit == trumpsuit else 0

	def MoveColliderect(self, XMotion: float, YMotion: float) -> None:
		self.colliderect.move_ip(XMotion, YMotion)

	@classmethod
	def UpdateAtrributes(cls) -> None:
		for card in cls.AllCardsList:
			card.image = cls.CardImages[repr(card)]
			card.surfandpos = (card.image, card.rect)

	@classmethod
	def AddImages(cls, RequiredResizeRatio: Fraction) -> None:
		cls.BaseCardImages = {ID: OpenImage(ID, RequiredResizeRatio) for ID in AllCardIDs}
		cls.CardImages = cls.BaseCardImages.copy()
		cls.UpdateAtrributes()

	# noinspection PyTypeChecker
	@classmethod
	def UpdateImages(cls, ResizeRatio: Fraction) -> None:
		cls.CardImages = CardResizer(ResizeRatio, tuple(cls.BaseCardImages.items()))
		cls.UpdateAtrributes()
