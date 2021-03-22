from __future__ import annotations

from typing import TYPE_CHECKING
from functools import lru_cache

from src.display.abstract_surfaces.knock_surface_with_cards import KnockSurfaceWithCards
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin
from src.display.faders import OpacityFader
from src.players.players_client import ClientPlayer as Player

if TYPE_CHECKING:
	from src.cards.client_card import ClientCard as Card


@lru_cache
def BoardDimensionsHelper(
		SurfWidth: int,
		SurfHeight: int,
		CardX: int,
		CardY: int,
		NormalLinesize: int,
		PlayerNo: int
):
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


@lru_cache
def BoardHeightHelper(
		Width: int,
		GameSurfHeight: int,
		WindowMargin: int,
		CardY: int
):
	return min(Width, (GameSurfHeight - WindowMargin - (CardY + 40)))


# noinspection PyAttributeOutsideInit
class BoardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	__slots__ = 'PlayerTextPositions', 'NonrelativeBoardCentre', 'StandardFont'

	def __init__(self):
		self.CardList = self.game.PlayedCards
		self.CardFadeManager = OpacityFader('OpaqueOpacity', 'Board')
		self.CardUpdateQueue = self.game.NewCardQueues.PlayedCards
		super().__init__()   # calls SurfDimensions()
		SurfaceCoordinator.BoardSurf = self

	def Initialise(self):
		self.StandardFont = self.Fonts['StandardBoardFont']
		return super().Initialise()

	def SurfDimensions(self):
		self.Width = self.GameSurf.Width // 2
		self.x = self.GameSurf.Height // 4
		self.y = self.WindowMargin
		self.Height = BoardHeightHelper(self.Width, self.GameSurf.Height, self.WindowMargin, self.CardY)

		W, H, X, Y, L, P = self.Width, self.Height, self.CardX, self.CardY, self.StandardFont.linesize, self.PlayerNo
		CardRects, self.PlayerTextPositions = BoardDimensionsHelper(W, H, X, Y, L, P)
		self.AddRectList(CardRects)

	def SurfAndPos(self):
		super().SurfAndPos()
		self.NonrelativeBoardCentre = (self.attrs.centre[0] + self.x, self.attrs.centre[1] + self.y)

	def UpdateCard(
			self,
			card: Card,
			index: int
	):
		card.ReceiveRect(self.RectList[self.game.PlayerOrder[index]])

	def GetSurfBlits(self):
		with self.game:
			WhoseTurnPlayerIndex, TrickInProgress, RoundLeaderIndex = self.game.GetAttributes(
				('WhoseTurnPlayerIndex', 'TrickInProgress', 'RoundLeaderIndex')
			)

		PlayerNo, CardList = self.PlayerNo, self.CardList
		AllBid, Linesize = Player.AllBid(), self.StandardFont.linesize
		Args = (WhoseTurnPlayerIndex, TrickInProgress, len(CardList), AllBid, PlayerNo, Linesize, RoundLeaderIndex)
		Positions = self.PlayerTextPositions
		T = sum([player.BoardText(*Args, *Positions[i]) for i, player in Player.enumerate()], start=[])
		return super().GetSurfBlits() + [self.GetText(t[0], t[1], center=t[2]) for t in T]
