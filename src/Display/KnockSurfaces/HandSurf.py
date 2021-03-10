from functools import lru_cache
from src.Display.AbstractSurfaces.KnockSurfaceWithCards import KnockSurfaceWithCards
from src.Display.Faders import OpacityFader


@lru_cache
def GetHandRects(GameSurfX, WindowMargin, CardX, StartNumber):
	"""
	@type GameSurfX: int
	@type WindowMargin: int
	@type CardX: int
	@type StartNumber: int
	"""

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
		self.CardFadeManager = OpacityFader('Hand')
		self.CardUpdateQueue = self.game.NewCardQueues.Hand
		super().__init__()   # calls SurfDimensions()
		self.HandRectsCalculated = False

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self):
		self.y = self.GameSurfHeight - (self.CardY + self.WindowMargin)
		self.Width = self.GameSurfWidth
		self.Height = self.CardY + self.WindowMargin

	def GetHandRects(self):
		self.AddRectList(GetHandRects(self.Width, self.WindowMargin, self.CardX, self.game.StartCardNumber))
		self.HandRectsCalculated = True

	def ClearRectList(self):
		self.RectList.clear()
		self.CoverRects.clear()
		self.HandRectsCalculated = False

	def UpdateCard(self, card, index):
		"""
		@type card: src.Cards.ClientCard.ClientCard
		@type index: int
		"""

		card.ReceiveRect(self.RectList[index], self.attrs.topleft, self.GameSurf.topleft, CardInHand=True)

	# Update & GetSurfBlits methods not defined here.
	# The base class doesn't need to be overridden.
