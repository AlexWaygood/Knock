from __future__ import annotations
from typing import TYPE_CHECKING, Tuple, List

from functools import lru_cache
from fractions import Fraction
from math import ceil

from src.display.abstract_surfaces.text_rendering import Fonts
from src.cards.client_card import ClientCard as Card

if TYPE_CHECKING:
	from src.players.players_client import ClientPlayer as Player
	from src.players.players_client import ClientGameplayers as Gameplayers

	from src.display.knock_surfaces.game_surf import GameSurface
	from src.display.knock_surfaces.board_surf import BoardSurface

	from src.game.client_game import ClientGame as Game
	from src.special_knock_types import Position, OptionalColours


@lru_cache
def GetDimensions(GameX, GameY, CurrentCardDimensions=Card.OriginalImageDimensions):
	"""This function is designed to be used both at the beginning of the game and midway through the game

	@type GameX: int
	@type GameY: int
	@type CurrentCardDimensions: Tuple[int, int]
	"""

	# Calculate the required size of the card images, based on various ratios of surfaces that will appear on the screen.
	# Lots of "magic numbers" here, based purely on the principle of "keep the proportions that look good on my laptop".

	WindowMargin = int(GameX * Fraction(15, 683))
	CardY = min(((GameY // Fraction(768, 150)) - WindowMargin), (GameY // 5.5))
	CardX, CardY = ceil(CardY * Fraction(*CurrentCardDimensions)), ceil(CardY)
	RequiredResizeRatio = CurrentCardDimensions[1] / CardY
	return WindowMargin, CardX, CardY, RequiredResizeRatio


class SurfaceCoordinator:
	__slots__ = tuple()

	game: Game = None
	player: Player = None
	gameplayers: Gameplayers = None
	GameSurf: GameSurface = None
	BoardSurf: BoardSurface = None
	Fonts: Fonts = None
	ColourScheme: OptionalColours = None
	PlayerNo = 0

	WindowMargin = 0
	CardX = 0
	CardY = 0

	BoardCentre: Position = tuple()
	PlayStartedInputPos: Position = tuple()
	PreplayInputPos: Position = tuple()

	AllSurfaces: List[SurfaceCoordinator] = []

	@classmethod
	def AddClassVars(
			cls,
			game: Game,
			player: Player,
			colour_scheme: OptionalColours,
			GameSurf: GameSurface
	):

		cls.game = game
		cls.ColourScheme = colour_scheme
		cls.player = player
		cls.gameplayers = game.gameplayers
		cls.PlayerNo = game.PlayerNumber
		cls.GameSurf = GameSurf
		cls.GameSurf.Hand = cls.player.Hand
		cls.Fonts = Fonts(GameSurf.Width, GameSurf.Height)

		cls.WindowMargin, cls.CardX, cls.CardY, RequiredResizeRatio = GetDimensions(GameSurf.Width, GameSurf.Height)
		Card.AddImages(RequiredResizeRatio)

	@classmethod
	def NewWindowSize1(cls):
		GameX, GameY = cls.GameSurf.Width, cls.GameSurf.Height

		cls.WindowMargin, cls.CardX, cls.CardY, RequiredResizeRatio = GetDimensions(
			GameX,
			GameY,
			CurrentCardDimensions=(cls.CardX, cls.CardY)
		)

		Card.AddImages(RequiredResizeRatio)
		cls.Fonts.__init__(cls.GameSurf.Width, cls.GameSurf.Height)

	@classmethod
	def NewWindowSize2(cls):
		for surf in cls.AllSurfaces:
			surf.Initialise()

		cls.BoardCentre = BoardX, BoardY = cls.BoardSurf.NonrelativeBoardCentre
		cls.PreplayInputPos = (cls.GameSurf.attrs.centre[0], (cls.GameSurf.attrs.centre[1] + 50))
		cls.PlayStartedInputPos = (BoardX, (BoardY + 50))

	@classmethod
	def NewWindowSize(
			cls,
			WindowX: int,
			WindowY: int,
			ResetPos: bool
	):

		cls.GameSurf.NewWindowSize(WindowX, WindowY, ResetPos)
		cls.NewWindowSize1()
		cls.NewWindowSize2()

	@classmethod
	def UpdateAll(cls, ForceUpdate: bool = False):
		for surf in cls.AllSurfaces:
			surf.Update(ForceUpdate=ForceUpdate)

	def Initialise(self):
		pass

	def Update(self, ForceUpdate: bool = False):
		pass
