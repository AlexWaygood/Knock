from typing import Union
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


def OpenImage(ID, ResizeRatio):
	"""
	@type ID: str
	@type ResizeRatio: float
	"""

	im = Image.open(path.join('..', '..', 'Images', 'Cards', f'{ID}.jpg')).convert("RGB")
	im = im.resize((int(im.size[0] / ResizeRatio), int(im.size[1] / ResizeRatio)))
	return image.fromstring(im.tobytes(), im.size, im.mode).convert()


@lru_cache
def CardResizer(ResizeRatio, BaseCardImages):
	"""
	@type ResizeRatio: float
	@type BaseCardImages: dict
	"""

	return {ID: rotozoom(cardimage, 0, (1 / ResizeRatio)) for ID, cardimage in BaseCardImages.items()}


# Imported by ClientGame script as well as being used here.
AllCardValues = product(Rank.AllRanks, Suit.CardSuits)


class ClientCard(Card):
	__slots__ = 'rect', 'colliderect', 'image', 'surfandpos'

	BaseCardImages = {}
	CardImages = {}

	def __new__(cls, rank, suit, PlayedBy=''):
		"""
		@type rank: Union[int, str]
		@type suit: str
		@type PlayedBy: str
		"""

		new = super(ClientCard, cls).__new__(cls, rank, suit)
		new.PlayedBy = PlayedBy
		return new

	def __init__(self, rank, suit):
		"""
		@rtype: object
		@type rank: Union[int, str]
		@type suit: str
		"""

		super().__init__(rank, suit)
		self.rect = Rect(0, 0, 1, 1)
		self.colliderect = self.rect
		self.image = self.CardImages[self.ID]
		self.surfandpos = (self.image, self.rect)

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
	def AddImages(cls, RequiredResizeRatio: float):
		cls.BaseCardImages = {f'{ID[0]}{ID[1]}': OpenImage(ID, RequiredResizeRatio) for ID in AllCardValues}
		cls.CardImages = cls.BaseCardImages.copy()

	@classmethod
	def UpdateImages(cls, ResizeRatio: float):
		cls.CardImages = CardResizer(ResizeRatio, cls.BaseCardImages)

		for card in cls.AllCards:
			card.image = cls.CardImages[repr(card)]
