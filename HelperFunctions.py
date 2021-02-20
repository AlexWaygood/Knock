"""A smattering of short functions (and one variable) to make the script cleaner in various other files."""

from PygameWrappers import FontAndLinesize, SurfaceAndPosition

from ipaddress import ip_address
import socket
from itertools import groupby
from datetime import datetime
from string import ascii_letters, digits, punctuation
from fractions import Fraction
from math import ceil
from functools import lru_cache
from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.font import SysFont
from pygame.transform import rotozoom


PrintableCharacters = ''.join((digits, ascii_letters, punctuation))
PrintableCharactersPlusSpace = PrintableCharacters + ' '


def GetTime():
	"""Function to get the time in a fixed format"""

	return datetime.now().strftime("%H:%M:%S")


def IPValidation(InputText):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = socket.gethostbyname(InputText)
		ip_address(address)

	return InputText


def AllEqual(Iterable):
	"""Does what it says on the tin"""

	g = groupby(Iterable)
	return next(g, True) and not next(g, False)


@lru_cache
def GetDimensions1(NewGameSurfDimensions, CurrentCardDimensions=(691, 1056)):
	"""This function is designed to be used both at the beginning of the game and midway through the game"""

	# Calculate the required size of the card images, based on various ratios of surfaces that will appear on the screen.
	# Lots of "magic numbers" here, based purely on the principle of "keep the proportions that look good on my laptop".

	GameX, GameY = NewGameSurfDimensions
	WindowMargin = int(GameX * Fraction(15, 683))
	ImpliedCardHeight = min(((GameY // Fraction(768, 150)) - WindowMargin), (GameY // 5.5))
	ImpliedCardWidth = ImpliedCardHeight * Fraction(*CurrentCardDimensions)
	NewCardDimensions = (ceil(ImpliedCardWidth), ceil(ImpliedCardHeight))
	RequiredResizeRatio = CurrentCardDimensions[1] / ImpliedCardHeight
	return WindowMargin, NewCardDimensions, RequiredResizeRatio


@lru_cache
def ResizeHelper(var1, var2, ScreenSize, i):
	var1 = ScreenSize[i] if var1 > ScreenSize[i] else var1
	var1 = 10 if var1 < 10 else var1
	ResizeNeeded = (var1 != var2)
	var2 = var1
	return var2, ResizeNeeded


@lru_cache
def FontMachine(DefaultFont, GameX, GameY):
	x = 10
	NormalFont = SysFont(DefaultFont, x, bold=True)
	UnderLineFont = SysFont(DefaultFont, x, bold=True)

	while x < 19:
		x += 1
		font = SysFont(DefaultFont, x, bold=True)
		font2 = SysFont(DefaultFont, x, bold=True)
		Size = font.size('Trick not in progress')

		if Size[0] > int(GameX * Fraction(70, 683)) or Size[1] > int(GameY * Fraction(18, 768)):
			break

		NormalFont = font
		UnderLineFont = font2

	UnderLineFont.set_underline(True)

	return {
			'Normal': FontAndLinesize(NormalFont),
			'UnderLine': FontAndLinesize(UnderLineFont),
			'Title': FontAndLinesize(SysFont(DefaultFont, 20, bold=True)),
			'Massive': FontAndLinesize(SysFont(DefaultFont, 40, bold=True))
		}


@lru_cache
def SurfMachine(ScoreboardColour, TrumpCardSurfaceDimensions, GameX, GameY, CardX, CardY, WindowMargin, TrumpCardPos,
                CoverRectOpacities, BoardPos, ScreenSize, CardRectsOnBoard, BlackFade):
	return {
		'Scoreboard': SurfaceAndPosition(
			[WindowMargin, WindowMargin],
			SurfaceDimensions=None,
			FillColour=ScoreboardColour
		),

		'TrumpCard': SurfaceAndPosition(
			[(GameX - (CardX + 50)), WindowMargin],
			SurfaceDimensions=TrumpCardSurfaceDimensions,
			RectList=(TrumpCardPos,),
			Dimensions=TrumpCardSurfaceDimensions,
			CoverRectOpacity=CoverRectOpacities['TrumpCard']
		),

		'Hand': SurfaceAndPosition(
			[0, (GameY - (CardY + WindowMargin))],
			SurfaceDimensions=(GameX, (CardY + WindowMargin)),
			CoverRectOpacity=CoverRectOpacities['Hand']
		),

		'Board': SurfaceAndPosition(
			BoardPos.copy(),
			SurfaceDimensions=(GameX, GameX),
			RectList=CardRectsOnBoard,
			CoverRectOpacity=CoverRectOpacities['Board']
		),

		'blackSurf': SurfaceAndPosition(
			[0, 0],
			SurfaceDimensions=ScreenSize,
			OpacityRequired=True,
			FillColour=BlackFade
		)
	}


@lru_cache
def CardResizer(ResizeRatio, BaseCardImages):
	return {ID: rotozoom(cardimage, 0, (1 / ResizeRatio)) for ID, cardimage in BaseCardImages.items()}


@lru_cache
def GetHandRects(GameSurfX, WindowMargin, CardX, StartNumber):
	x = WindowMargin
	DoubleWindowMargin = x * 2
	PotentialBuffer = CardX // 2

	if ((CardX * StartNumber) + DoubleWindowMargin + (PotentialBuffer * (StartNumber - 1))) < GameSurfX:
		CardBufferInHand = PotentialBuffer
	else:
		CardBufferInHand = min(x, ((GameSurfX - DoubleWindowMargin - (CardX * StartNumber)) // (StartNumber - 1)))

	return [((x + (i * (CardX + CardBufferInHand))), 0) for i in range(StartNumber)]


@lru_cache
def GetDimensions2Helper(GameX, GameY, CardX, CardY, WindowMargin, NormalLinesize, PlayerNo):
	ErrorPos = (int(GameX * Fraction(550, 683)), int(GameY * Fraction(125, 192)))

	BoardWidth = GameX // 2
	BoardPos = [(GameX // 4), WindowMargin]
	BoardHeight = min(BoardWidth, (GameY - BoardPos[1] - (CardY + 40)))
	BoardFifth = BoardHeight // 5

	BoardCentre = (BoardWidth, ((BoardHeight // 2) + WindowMargin))
	TripleLinesize = 3 * NormalLinesize
	TwoFifthsBoard, ThreeFifthsBoard = (BoardFifth * 2), (BoardFifth * 3)
	HalfCardWidth, DoubleCardWidth = (CardX // 2), (CardX * 2)

	# Top-left position & top-right position
	PlayerTextPositions = [
		(CardX, int(TwoFifthsBoard - TripleLinesize)),
		((BoardWidth - CardX), int(TwoFifthsBoard - TripleLinesize))
	]

	# Top-left position & top-right position
	CardRectsOnBoard = [
		((CardX + HalfCardWidth), (PlayerTextPositions[0][1] - HalfCardWidth)),
		((BoardWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[1][1] - HalfCardWidth))
	]

	if PlayerNo != 2:
		BoardMid = BoardWidth // 2

		if PlayerNo != 4:
			# Top-middle position
			PlayerTextPositions.insert(1, (BoardMid, (NormalLinesize // 2)))
			CardRectsOnBoard.insert(1, ((BoardMid - HalfCardWidth), (PlayerTextPositions[1][1] + (NormalLinesize * 4))))

		if PlayerNo != 3:
			# Bottom-right position
			PlayerTextPositions.append(((BoardWidth - CardX), ThreeFifthsBoard))
			CardRectsOnBoard.append(((BoardWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[-1][1] - HalfCardWidth)))

			# Bottom-mid position
			if PlayerNo != 4:
				PlayerTextPositions.append((BoardMid, int(BoardHeight - (NormalLinesize * 5))))
				CardRectsOnBoard.append(((BoardMid - HalfCardWidth), (PlayerTextPositions[-1][1] - CardY - NormalLinesize)))

			# Bottom-left position
			if PlayerNo != 5:
				PlayerTextPositions.append((CardX, ThreeFifthsBoard))
				CardRectsOnBoard.append((DoubleCardWidth, (PlayerTextPositions[-1][1] - HalfCardWidth)))

	TrumpCardSurfaceDimensions = ((CardX + 2), (CardY + int(NormalLinesize * 2.5) + 10))
	TrumpCardPos = (1, int(NormalLinesize * 2.5))

	return TrumpCardPos, TrumpCardSurfaceDimensions, CardRectsOnBoard, ErrorPos, BoardCentre, PlayerTextPositions, \
	       BoardPos
