from typing import Sequence, Any, MutableMapping
from SurfacesHelperFunctions import BoardDimensionsHelper, TrumpCardDimensionsHelper
from HelperFunctions import GetHandRects
from SurfaceBaseClasses import KnockSurface, KnockSurfaceWithCards, TextBlitsMixin


class HandSurface(KnockSurfaceWithCards):
	__slots__ = 'WindowMargin'
	x = 0

	def __init__(self, FillColour, GameSurfWidth, GameSurfHeight, WindowMargin, CardY):
		super().__init__(FillColour, GameSurfWidth, GameSurfHeight, WindowMargin, CardY)

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self, GameSurfWidth, GameSurfHeight, WindowMargin, CardY, *args, **kwargs):
		self.y = GameSurfHeight - (CardY + WindowMargin)
		self.SurfWidth = GameSurfWidth
		self.SurfHeight = CardY + WindowMargin
		self.WindowMargin = WindowMargin

	def GetHandRects(self, CardX, CardY, StartCardNumber):
		self.AddCardRects(
			GetHandRects(self.SurfWidth, self.WindowMargin, CardX, StartCardNumber),
			CardX,
			CardY
		)

	def UpdateCardOnArrival(self, index, card, *args, **kwargs):
		card.ReceiveRect(self.RectList[index])

	def NewWindowSize(self, GameSurfWidth, GameSurfHeight, WindowMargin, CardY, cards):
		self.InitialiseSurf(self.colour, GameSurfWidth, GameSurfHeight, WindowMargin, CardY)

		with self:
			self.Update(0, ForceUpdate=True, cards=cards)

	# Update method not defined here as Update for the base class doesn't need to be overridden


class BoardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	__slots__ = 'PlayerTextPositions', 'NonrelativeBoardCentre'

	def __init__(self, FillColour, GameSurfWidth, GameSurfHeight, WindowMargin, CardX, CardY, NormalLinesize, PlayerNo):
		super().__init__(
			FillColour,
			GameSurfWidth,
			GameSurfHeight,
			WindowMargin,
			CardX,
			CardY,
			NormalLinesize,
			PlayerNo
		)

		self.TextColour = (0, 0, 0)

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self, GameSurfWidth, GameSurfHeight, WindowMargin,
	                   CardX, CardY, NormalLinesize, PlayerNo):

		self.SurfWidth = GameSurfWidth // 2
		self.x = GameSurfWidth // 4
		self.y = WindowMargin
		self.SurfHeight = min(self.SurfWidth, (GameSurfHeight - WindowMargin - (CardY + 40)))

		W, H, X, Y = self.SurfWidth, self.SurfHeight, CardX, CardY
		CardRects, self.PlayerTextPositions = BoardDimensionsHelper(W, H, X, Y,	NormalLinesize, PlayerNo)
		self.AddCardRects(CardX, CardY, CardRects)
		self.NonrelativeBoardCentre = (self.centre[0] + self.x, self.centre[1] + self.y)

	def NewWindowSize(self, GameSurfWidth, GameSurfHeight, WindowMargin, CardX, CardY, NormalLineSize, PlayerNo, cards,
	                  FontDict, players, WhoseTurnPlayerIndex, TrickInProgress, RoundLeaderIndex):

		self.InitialiseSurf(
			self.colour,
			GameSurfWidth,
			GameSurfHeight,
			WindowMargin,
			CardX,
			CardY,
			NormalLineSize,
			PlayerNo
		)

		with self:
			self.Update(
				0,
				ForceUpdate=True,
				cards=cards,
				FontDict=FontDict,
				players=players,
				WhoseTurnPlayerIndex=WhoseTurnPlayerIndex,
				TrickInProgress=TrickInProgress,
				RoundLeaderIndex=RoundLeaderIndex
			)

	def UpdateCardOnArrival(self, index, card, PlayerOrder: Sequence = tuple(), *args, **kwargs):
		card.ReceiveRect(self.RectList[PlayerOrder[index]])

	def GetSurfBlits(self, cards, FontDict: MutableMapping = None, players: Any = tuple(), WhoseTurnPlayerIndex=-1,
	                 TrickInProgress=False, RoundLeaderIndex=-1):

		AllBid, PlayerNo, Linesize = players.AllBid(), players.PlayerNo, FontDict['Normal'].linesize
		Args = (WhoseTurnPlayerIndex, TrickInProgress, len(cards), AllBid, PlayerNo, Linesize, RoundLeaderIndex)
		Positions = self.PlayerTextPositions
		T = sum([player.BoardText(*Args, *Positions[i]) for i, player in enumerate(players)], start=[])

		return [self.GetText(t[0], t[1], center=t[2]) for t in T]

	def Update(self, ServerIteration, ForceUpdate=False, cards: Sequence = tuple(),
	             FontDict: MutableMapping = None, players: Any = tuple(), WhoseTurnPlayerIndex=-1,
	             TrickInProgress=False, RoundLeaderIndex=-1):

		return super().Update(
			ServerIteration,
			cards,
			FontDict,
			players,
			WhoseTurnPlayerIndex,
			TrickInProgress,
			RoundLeaderIndex
		)


class TrumpCardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	# Slots not defined as no more are required

	def __init__(self, FillColour, GameSurfWidth, WindowMargin, CardX, CardY, NormalLinesize):
		super().__init__(FillColour, GameSurfWidth, WindowMargin, CardX, CardY, NormalLinesize)
		self.TextColour = (0, 0, 0)

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self, GameSurfWidth, WindowMargin, CardX, CardY, NormalLinesize):
		Vals = TrumpCardDimensionsHelper(GameSurfWidth, CardX, CardY, NormalLinesize)
		self.x, self.SurfWidth, self.SurfHeight, TrumpCardPos = Vals
		self.y = WindowMargin
		self.AddCardRects(CardX, CardY, (TrumpCardPos,))

	def NewWindowSize(self, GameSurfWidth, WindowMargin, CardX, CardY, NormalLinesize, cards, NormalFont):
		self.InitialiseSurf(self.colour, GameSurfWidth, WindowMargin, CardX, CardY, NormalLinesize)

		with self:
			self.Update(0, ForceUpdate=True, cards=cards, NormalFont=NormalFont)

	def UpdateCardOnArrival(self, index, card, *args, **kwargs):
		card.ReceiveRect(self.RectList[0])

	def GetSurfBlits(self, cards, NormalFont=None, *args, **kwargs):
		return [self.GetText('TrumpCard', NormalFont, center=((self.centre[0] / 2), (NormalFont.linesize / 2)))]

	def Update(self, ServerIteration, ForceUpdate=False, cards: Sequence = tuple(), NormalFont=None, *args, **kwargs):
		return super().Update(ServerIteration, cards, NormalFont)


class Scoreboard(KnockSurface, TextBlitsMixin):
	__slots__ = 'LeftMargin', 'title'

	def __init__(self, FillColour, FontDict, players, GamesPlayed, WindowMargin):
		super().__init__(FillColour, WindowMargin, FontDict, players, GamesPlayed)

	# noinspection PyAttributeOutsideInit
	def SurfDimensions(self, WindowMargin, FontDict, players, GamesPlayed, *args, **kwargs):
		self.x = WindowMargin
		self.y = WindowMargin
		NormalLineSize = FontDict['Normal'].linesize
		self.LeftMargin = int(NormalLineSize * 1.75)
		MaxPointsText = max(FontDict['Normal'].size(f'{str(player)}: 88 points')[0] for player in players)
		self.TextColour = (0, 0, 0)

		self.SurfWidth = (
				(2 * self.LeftMargin)
				+ max(MaxPointsText, FontDict['UnderLine'].size('Trick not in progress')[0])
		)

		Multiplier = ((players.PlayerNo * 2) + 7) if GamesPlayed else (players.PlayerNo + 4)
		self.SurfHeight = (NormalLineSize * Multiplier) + (2 * self.LeftMargin)
		self.title = (FontDict['Underline'].render('SCOREBOARD'), (self.centre[0], int(NormalLineSize * 1.5)))

	def NewWindowSize(self, WindowMargin, FontDict, players, GamesPlayed, TrickNo, CardNo, RoundNo, StartCardNo):
		self.InitialiseSurf(self.colour, WindowMargin, FontDict, players, GamesPlayed)

		with self:
			self.Update(0, ForceUpdate=True, FontDict=FontDict, players=players, TrickNo=TrickNo,
			            CardNo=CardNo, RoundNo=RoundNo, StartCardNo=StartCardNo, GamesPlayed=GamesPlayed)

	def TextBlitsHelper(self, y, ScoreboardBlits, Gen, NormalFont):
		for Message in Gen:
			args = ({'topleft': (self.LeftMargin, y)}, {'topright': ((self.SurfWidth - self.LeftMargin), y)})
			ScoreboardBlits += [self.GetText(Message[i], NormalFont, **arg) for i, arg in enumerate(args)]
			y += NormalFont.linesize

		return ScoreboardBlits, y

	def GetSurfBlits(self, FontDict, players, TrickNo, CardNo, RoundNo, StartCardNo, GamesPlayed):
		ScoreboardBlits = [self.title]
		NormalFont, NormalLineSize = FontDict['Normal'], FontDict['Normal'].linesize
		y = self.title[1] + NormalLineSize
		ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, players.ScoreboardText(), NormalFont)
		y += NormalLineSize * 2

		Message1 = self.GetText(f'Round {RoundNo} of {StartCardNo}', NormalFont, center=(self.centre[0], y))
		TrickText = f'Trick {TrickNo} of {CardNo}' if TrickNo else 'Trick not in progress'
		Message2 = self.GetText(TrickText, NormalFont, center=(self.centre[0], (y + NormalLineSize)))
		ScoreboardBlits += [Message1, Message2]

		if GamesPlayed:
			y += NormalLineSize * 3
			ScoreboardBlits.append(self.GetText('-----', NormalFont, center=(self.centre[0], y)))
			y += NormalLineSize
			ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, players.ScoreboardText2(), NormalFont)

		return ScoreboardBlits

	def Update(self, ServerIteration, ForceUpdate=False, FontDict=None, players: Any = tuple(),
	             TrickNo=-1, CardNo=-1, RoundNo=-1, StartCardNo=0, GamesPlayed=-1, *args, **kwargs):

		return super().Update(ServerIteration, FontDict, players, TrickNo, CardNo, RoundNo, StartCardNo, GamesPlayed)
