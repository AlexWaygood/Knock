from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from PIL import Image
from functools import lru_cache
from itertools import product

from src.cards.server_card import ServerCard as Card
from src.cards.rank import Rank
from src.cards.suit import Suit

from os import environ, path
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect
from pygame.transform import rotozoom
from pygame.image import fromstring as pg_image_fromstring

if TYPE_CHECKING:
	from pygame import Surface
	from src.special_knock_types import RankType, Position, CardImageDict, TupledImageDict
	from fractions import Fraction


def OpenImage(ID: str,
              ResizeRatio: Fraction):

	im = Image.open(path.join(ClientCard.PathToImages, f'{ID}.jpg')).convert("RGB")
	im = im.resize((int(im.size[0] / ResizeRatio), int(im.size[1] / ResizeRatio)))
	return pg_image_fromstring(im.tobytes(), im.size, im.mode).convert()


@lru_cache
def CardResizer(ResizeRatio: Fraction,
                BaseCardImages: TupledImageDict):

	return {ID: rotozoom(cardimage, 0, (1 / ResizeRatio)) for ID, cardimage in BaseCardImages}


# Imported by ClientGame script.
AllCardValues = product(Rank.AllRanks, Suit.CardSuits)
AllCardIDs = [f'{ID[0]}{ID[1]}' for ID in AllCardValues]


class ClientCard(Card):
	__slots__ = 'rect', 'colliderect', 'image', 'surfandpos'

	BaseCardImages: CardImageDict = {}
	CardImages: CardImageDict = {}
	OriginalImageDimensions = (691, 1056)
	PathToImages = path.join('Images', 'Cards', 'Compressed')

	def __new__(cls,
	            rank: RankType,
	            suit: str,
	            PlayedBy: str = ''):

		new = super(ClientCard, cls).__new__(cls, rank, suit)
		new.PlayedBy = PlayedBy
		return new

	def __init__(self,
	             rank: RankType,
	             suit: str):

		super().__init__(rank, suit)
		self.rect = Rect(0, 0, 1, 1)
		self.colliderect = self.rect
		self.image: Optional[Surface] = None
		self.surfandpos = tuple()

	def ReceiveRect(self,
	                rect: Rect,
	                SurfPos: Position = None,
	                GameSurfPos: Position = None,
	                CardInHand: bool = False):

		self.rect = rect
		self.surfandpos = (self.image, self.rect)

		if CardInHand:
			self.colliderect = rect.move(*SurfPos).move(*GameSurfPos)

	def GetWinValue(self,
	                playedsuit: Suit,
	                trumpsuit: Suit):

		if self.Suit == playedsuit:
			return self.Rank.Value
		return self.Rank.Value + 13 if self.Suit == trumpsuit else 0

	@classmethod
	def UpdateAtrributes(cls):
		for card in cls.AllCards:
			try:
				card.image = cls.CardImages[repr(card)]
			except Exception as e:
				print(f'Path is {path.abspath(cls.PathToImages)}')
				print(cls.BaseCardImages)
				print(AllCardValues)
				raise e
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
