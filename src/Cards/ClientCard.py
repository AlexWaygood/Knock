from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Dict
from PIL import Image
from functools import lru_cache
from itertools import product

from src.Cards.ServerCard import ServerCard as Card
from src.Cards.Rank import Rank
from src.Cards.Suit import Suit

from os import environ, path
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Rect
from pygame.transform import rotozoom
from pygame import image

if TYPE_CHECKING:
	from pygame import Surface
	from src.SpecialKnockTypes import RankType


def OpenImage(ID, ResizeRatio):
	"""
	@type ID: str
	@type ResizeRatio: float
	"""

	im = Image.open(path.join(ClientCard.PathToImages, f'{ID}.jpg')).convert("RGB")
	im = im.resize((int(im.size[0] / ResizeRatio), int(im.size[1] / ResizeRatio)))
	return image.fromstring(im.tobytes(), im.size, im.mode).convert()


@lru_cache
def CardResizer(ResizeRatio: float,
                BaseCardImages: Dict[str: Surface]):

	return {ID: rotozoom(cardimage, 0, (1 / ResizeRatio)) for ID, cardimage in BaseCardImages.items()}


# Imported by ClientGame script.
AllCardValues = product(Rank.AllRanks, Suit.CardSuits)
AllCardIDs = [f'{ID[0]}{ID[1]}' for ID in AllCardValues]


class ClientCard(Card):
	__slots__ = 'rect', 'colliderect', 'image', 'surfandpos'

	BaseCardImages = {}
	CardImages = {}
	OriginalImageDimensions = (691, 1056)
	PathToImages = path.join('Images', 'Cards')

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

	def ReceiveRect(self, rect, SurfPos=None, GameSurfPos=None, CardInHand=False):
		"""
		@type rect: Rect
		@type SurfPos: tuple
		@type GameSurfPos: tuple
		@type CardInHand: bool
		"""

		self.rect = rect
		self.surfandpos = (self.image, self.rect)

		if CardInHand:
			self.colliderect = rect.move(*SurfPos).move(*GameSurfPos)

	def GetWinValue(self, playedsuit, trumpsuit):
		"""
		@type playedsuit: Suit
		@type trumpsuit: Suit
		"""

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
	def AddImages(cls, RequiredResizeRatio: float):
		cls.BaseCardImages = {ID: OpenImage(ID, RequiredResizeRatio) for ID in AllCardIDs}
		cls.CardImages = cls.BaseCardImages.copy()
		cls.UpdateAtrributes()

	@classmethod
	def UpdateImages(cls, ResizeRatio: float):
		cls.CardImages = CardResizer(ResizeRatio, cls.BaseCardImages)
		cls.UpdateAtrributes()
