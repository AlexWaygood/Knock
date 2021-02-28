from GameSurface import GameSurface
from Surfaces import Scoreboard, TrumpCardSurface, HandSurface, BoardSurface
from DataContainers import Typewriter, UserInput
from HelperFunctions import FontMachine, GetDimensions1
from ContextHelpers import InputContext
from typing import List


class DisplayManager(object):
	__slots__ = 'fonts', 'BoardSurf', 'ScoreboardSurf', 'HandSurf', 'TrumpCardSurf', 'Members', 'Typewriter', \
	            'UserInput', 'PreplayInputPos', 'PlayStartedInputPos', 'InputContext', 'GameSurf', 'DefaultFont', \
	            'PlayerNo'

	def __init__(self, FillColour, WindowX, WindowY, DefaultFont, MinRectWidth, MinRectHeight, players):
		self.DefaultFont = DefaultFont
		self.PlayerNo = players.PlayerNo
		self.GameSurf = GameSurface(FillColour, WindowX, WindowY, MinRectWidth, MinRectHeight)
		self.fonts = FontMachine(DefaultFont, WindowX, WindowY)

		WindowMargin, CardX, CardY, RequiredResizeRatio = GetDimensions1(WindowX, WindowY)
		CommonArgs = (FillColour, WindowX, WindowY, WindowMargin)
		NormalLinesize = self.fonts['Normal'].linesize

		self.BoardSurf = BoardSurface(*CommonArgs, CardX, CardY, NormalLinesize, players.PlayerNo)
		self.ScoreboardSurf = Scoreboard(FillColour, self.fonts, players, 0, WindowMargin)
		self.HandSurf = HandSurface(*CommonArgs, CardY)
		self.TrumpCardSurf = TrumpCardSurface(FillColour, WindowX, WindowMargin, CardX, CardY, NormalLinesize)

		self.Members = (self.BoardSurf, self.ScoreboardSurf, self.HandSurf, self.TrumpCardSurf)

		self.Typewriter = Typewriter()
		self.UserInput = UserInput('', False)

		BoardX, BoardY = self.BoardSurf.NonrelativeBoardCentre
		self.PlayStartedInputPos = (BoardX, (BoardY + 50))
		self.PreplayInputPos = (self.GameSurf.centre[0], (self.GameSurf.centre[1] + 50))

		self.InputContext = InputContext()

	def Blits(self, L: List):
		self.GameSurf.surf.blits(L)

	def Update(self, ServerIterations, CardsOnBoard, players, WhoseTurnPlayerIndex, TrumpCard, CardsInHand,
	           TrickInProgress, RoundLeaderIndex, TrickNo, RoundNo, CardNo, StartCardNo, GamesPlayed, PlayStarted):

		self.GameSurf.fill()

		ArgTuple = (
			(CardsOnBoard, self.fonts, players, WhoseTurnPlayerIndex, TrickInProgress, RoundLeaderIndex),
			(self.fonts, players, TrickNo, CardNo, RoundNo, StartCardNo, GamesPlayed),
			(self.fonts['Normal'], TrumpCard),
			(CardsInHand,)
		)

		for surf, surfname, argtup in zip(self.Members, ('Board', 'Scoreboard', 'TrumpCard', 'Hand'), ArgTuple):
			with surf:
				surf.Update(ServerIterations[surfname], *argtup)
				self.Blits([surf.surfandpos])

		centre = self.GameSurf.centre
		TypewriterCentre = self.BoardSurf.NonrelativeBoardCentre if PlayStarted else centre
		self.Blits(self.Typewriter.GetTypedText(self.fonts['Normal'], TypewriterCentre))

		if self.InputContext.TypingNeeded:
			InputPos = self.PlayStartedInputPos if PlayStarted else self.PreplayInputPos
			self.Blits(self.UserInput.GetText(self.fonts['Normal'], InputPos))

		MessagePos = self.BoardSurf.NonrelativeBoardCentre if PlayStarted else centre
		self.Blits(self.InputContext.GetMessage(self.fonts, MessagePos))

	def NewWindowSize(self, WindowX, WindowY, ResetPos: int, FontDict, players, GamesPlayed, ServerIterations,
	                  CardsOnBoard, WhoseTurnPlayerIndex, TrumpCard, CardsInHand, TrickInProgress, RoundLeaderIndex,
	                  TrickNo, RoundNo, CardNo, StartCardNo, PlayStarted):

		self.GameSurf.NewWindowSize(WindowX, WindowY, ResetPos)
		GameX, GameY = self.GameSurf.SurfWidth, self.GameSurf.SurfHeight

		self.fonts = FontMachine(self.DefaultFont, GameX, GameY)

		WindowMargin, CardX, CardY, RequiredResizeRatio = GetDimensions1(WindowX, WindowY)
		CommonArgs = (WindowX, WindowY, WindowMargin)
		NormalLinesize = self.fonts['Normal'].linesize

		ArgTuple = (
			(*CommonArgs, CardX, CardY, NormalLinesize, self.PlayerNo),
			(WindowMargin, FontDict, players, GamesPlayed),
			(*CommonArgs, CardY),
			(GameX, WindowMargin, CardX, CardY, NormalLinesize)
		)

		for surf, argtup in zip(self.Members, ArgTuple):
			surf.InitialiseSurf(*argtup)

		self.Update(ServerIterations, CardsOnBoard, players, WhoseTurnPlayerIndex, TrumpCard, CardsInHand,
		            TrickInProgress, RoundLeaderIndex, TrickNo, RoundNo, CardNo, StartCardNo, GamesPlayed, PlayStarted)
