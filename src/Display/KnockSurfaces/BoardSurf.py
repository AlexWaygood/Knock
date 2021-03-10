from src.Display.AbstractSurfaces.KnockSurfaceWithCards import KnockSurfaceWithCards
from src.Display.Faders import OpacityFader
from src.Display.AbstractSurfaces.TextRendering import TextBlitsMixin
from functools import lru_cache


@lru_cache
def BoardDimensionsHelper(SurfWidth, SurfHeight, CardX, CardY, NormalLinesize, PlayerNo):
	"""
	@type SurfWidth: int
	@type SurfHeight: int
	@type CardX: int
	@type CardY: int
	@type NormalLinesize: int
	@type PlayerNo: int
	"""

	BoardFifth = SurfHeight // 5

	TripleLinesize = 3 * NormalLinesize
	TwoFifthsBoard, ThreeFifthsBoard = (BoardFifth * 2), (BoardFifth * 3)
	HalfCardWidth, DoubleCardWidth = (CardX // 2), (CardX * 2)

	PlayerTextPositions = [
		(CardX, int(TwoFifthsBoard - TripleLinesize)),
		((SurfWidth - CardX), int(TwoFifthsBoard - TripleLinesize))
	]

	# Top-left position & top-right position
	CardRectsOnBoard = [
		((CardX + HalfCardWidth), (PlayerTextPositions[0][1] - HalfCardWidth)),
		((SurfWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[1][1] - HalfCardWidth))
	]

	if PlayerNo != 2:
		BoardMid = SurfWidth // 2

		if PlayerNo != 4:
			# Top-middle position
			PlayerTextPositions.insert(1, (BoardMid, (NormalLinesize // 2)))
			CardRectsOnBoard.insert(1, (
				(BoardMid - HalfCardWidth), (PlayerTextPositions[1][1] + (NormalLinesize * 4))))

		if PlayerNo != 3:
			# Bottom-right position
			PlayerTextPositions.append(((SurfWidth - CardX), ThreeFifthsBoard))
			CardRectsOnBoard.append(
				((SurfWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[-1][1] - HalfCardWidth)))

			# Bottom-mid position
			if PlayerNo != 4:
				PlayerTextPositions.append((BoardMid, int(SurfHeight - (NormalLinesize * 5))))
				CardRectsOnBoard.append(
					((BoardMid - HalfCardWidth), (PlayerTextPositions[-1][1] - CardY - NormalLinesize)))

			# Bottom-left position
			if PlayerNo != 5:
				PlayerTextPositions.append((CardX, ThreeFifthsBoard))
				CardRectsOnBoard.append((DoubleCardWidth, (PlayerTextPositions[-1][1] - HalfCardWidth)))

	return CardRectsOnBoard, PlayerTextPositions


# noinspection PyAttributeOutsideInit
class BoardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	__slots__ = 'PlayerTextPositions', 'NonrelativeBoardCentre', 'StandardBoardFont'

	def __init__(self):
		self.CardList = self.game.PlayedCards
		self.CardFadeManager = OpacityFader('Board')
		super().__init__()   # calls SurfDimensions()

	def Initialise(self):
		super().Initialise()
		self.StandardFont = self.Fonts['StandardBoardFont']

	def SurfDimensions(self):
		self.SurfWidth = self.GameSurfWidth // 2
		self.x = self.GameSurfHeight // 4
		self.y = self.WindowMargin
		self.SurfHeight = min(self.SurfWidth, (self.GameSurfHeight - self.WindowMargin - (self.GameSurfHeight + 40)))

		W, H, X, Y, L = self.SurfWidth, self.SurfHeight, self.CardX, self.CardY, self.StandardFont.linesize
		CardRects, self.PlayerTextPositions = BoardDimensionsHelper(W, H, X, Y, L, self.PlayerNo)
		self.AddRectList(CardRects)
		self.NonrelativeBoardCentre = (self.attrs.centre[0] + self.x, self.attrs.centre[1] + self.y)

	def UpdateCard(self, card, index):
		"""
		@type card: src.Cards.ClientCard.ClientCard
		@type index: int
		"""

		card.ReceiveRect(self.RectList[self.game.PlayerOrder[index]])

	def GetSurfBlits(self):
		with self.game:
			players, PlayerNo, WhoseTurnPlayerIndex, TrickInProgress, RoundLeaderIndex = self.game.GetAttributes(
				('gameplayers', 'PlayerNo', 'WhoseTurnPlayerIndex', 'TrickInProgress', 'RoundLeaderIndex')
			)

		AllBid, Linesize = players.AllBid(), self.StandardFont.linesize
		Args = (WhoseTurnPlayerIndex, TrickInProgress, len(self.CardList), AllBid, PlayerNo, Linesize, RoundLeaderIndex)
		Positions = self.PlayerTextPositions
		T = sum([player.BoardText(*Args, *Positions[i]) for i, player in enumerate(players)], start=[])
		return super().GetSurfBlits() + [self.GetText(t[0], t[1], center=t[2]) for t in T]
