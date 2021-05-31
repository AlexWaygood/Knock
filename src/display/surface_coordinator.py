from __future__ import annotations
from typing import TYPE_CHECKING, List, Tuple

from functools import lru_cache
from fractions import Fraction
from math import ceil

from src.display.abstract_text_rendering import Fonts
from src.display.colours import ColourScheme

from src.cards.client_card import ClientCard as Card
from src.game.client_game import ClientGame as Game
from src.network.network_client import Client
from src.global_constants import ORIGINAL_CARD_IMAGE_DIMENSIONS

if TYPE_CHECKING:
	from src.players.players_client import ClientPlayer as Player
	from src.display.knock_surfaces.game_surf import GameSurface
	from src.display.knock_surfaces.board_surf import BoardSurface
	from src.special_knock_types import Position, DimensionTuple, SurfaceCoordinatorTypeVar


INPUT_POS_OFFSET = 50


@lru_cache
def GetDimensions(
		GameX: int,
		GameY: int,
		CurrentCardDimensions: DimensionTuple = ORIGINAL_CARD_IMAGE_DIMENSIONS
) -> Tuple[int, int, int, Fraction]:

	"""This function is designed to be used both at the beginning of the game and midway through the game"""

	# Calculate the required size of the card images, based on various ratios of surfaces that will appear on the screen.
	# Lots of "magic numbers" here, based purely on the principle of "keep the proportions that look good on my laptop".

	WindowMargin = int(GameX * Fraction(15, 683))
	CardY = min(((GameY // Fraction(768, 150)) - WindowMargin), (GameY // 5.5))
	CardX, CardY = ceil(CardY * Fraction(*CurrentCardDimensions)), ceil(CardY)
	RequiredResizeRatio = Fraction(CurrentCardDimensions[1], CardY)
	return WindowMargin, CardX, CardY, RequiredResizeRatio


class SurfaceCoordinator:
	__slots__ = tuple()

	game: Game = None
	player: Player = None
	GameSurf: GameSurface = None  # Will add itself as a class attribute in its own __init__()
	BoardSurf: BoardSurface = None  # Will add itself as a class attribute in its own __init__()
	Fonts: Fonts = None
	client: Client = None
	ColourScheme: ColourScheme = None
	PlayerNo = 0

	WindowMargin = 0
	CardX = 0
	CardY = 0
	RequiredResizeRatio: Fraction = None

	BoardCentre: Position = tuple()
	PlayStartedInputPos: Position = tuple()
	PreplayInputPos: Position = tuple()

	AllSurfaces: List[SurfaceCoordinator] = []

	@classmethod
	def AddClassVars(cls, player: Player) -> None:
		cls.game = Game.OnlyGame
		cls.client = Client.OnlyClient
		cls.ColourScheme = ColourScheme.OnlyColourScheme
		cls.player = player
		cls.PlayerNo = Game.PlayerNumber
		cls.GameSurf.Hand = cls.player.Hand
		GameX, GameY = cls.GameSurf.Width, cls.GameSurf.Height
		cls.Fonts = Fonts(GameX, GameY)
		cls.WindowMargin, cls.CardX, cls.CardY, cls.RequiredResizeRatio = GetDimensions(GameX, GameY)

	@classmethod
	def AddSurfs(cls) -> None:
		for surf in cls.AllSurfaces:
			surf.GetSurf()

		Card.AddImages(cls.RequiredResizeRatio)

	@classmethod
	def NewWindowSize1(cls) -> None:
		GameX, GameY = cls.GameSurf.Width, cls.GameSurf.Height

		cls.WindowMargin, cls.CardX, cls.CardY, RequiredResizeRatio = GetDimensions(
			GameX,
			GameY,
			CurrentCardDimensions=(cls.CardX, cls.CardY)
		)

		Card.UpdateImages(RequiredResizeRatio)
		cls.Fonts.__init__(cls.GameSurf.Width, cls.GameSurf.Height)

	@classmethod
	def NewWindowSize2(cls) -> None:
		for surf in cls.AllSurfaces:
			surf.Initialise().GetSurf()

		cls.BoardCentre = BoardX, BoardY = cls.BoardSurf.NonrelativeBoardCentre
		cls.PreplayInputPos = (cls.GameSurf.attrs.centre[0], (cls.GameSurf.attrs.centre[1] + INPUT_POS_OFFSET))
		cls.PlayStartedInputPos = (BoardX, (BoardY + INPUT_POS_OFFSET))

	@classmethod
	def NewWindowSize(
			cls,
			WindowX: int,
			WindowY: int,
			ResetPos: bool
	) -> None:

		cls.GameSurf.NewWindowSize(WindowX, WindowY, ResetPos)
		cls.NewWindowSize1()
		cls.NewWindowSize2()

	@classmethod
	def UpdateAll(cls, ForceUpdate: bool = False) -> None:
		if not cls.client.ConnectionBroken:
			for surf in cls.AllSurfaces:
				surf.Update(ForceUpdate=ForceUpdate)

	def Initialise(self: SurfaceCoordinatorTypeVar) -> SurfaceCoordinatorTypeVar:
		return self

	def Update(self, ForceUpdate: bool = False) -> None:
		pass

	def GetSurf(self) -> None:
		pass
