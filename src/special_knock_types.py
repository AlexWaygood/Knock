from __future__ import annotations
from typing import List, Callable, Tuple, TYPE_CHECKING, Union, Optional, Sequence, Dict, Any


if TYPE_CHECKING:
	from pygame import Surface, Rect
	from socket import socket

	from src.display.display_manager import DisplayManager
	from src.display.abstract_surfaces.knock_surface_with_cards import CoverRect
	from src.display.colours import ColourScheme
	from src.display.faders import ColourFader

	from src.players.players_abstract import Player
	from src.players.players_server import ServerPlayer

	from src.network.network_server import Server
	from src.network.network_client import Client

	from src.game.client_game import ClientGame
	from src.cards.server_card_suit_rank import ServerCard, Suit

	Blittable = Optional[Tuple[Surface, Rect]]
	BlitsList = Union[List[Blittable], Sequence[Blittable]]

	OptionalRect = Optional[Rect]
	RectList = List[OptionalRect]
	CoverRectList = List[Optional[CoverRect]]

	OptionalSurface = Optional[Surface]
	SurfaceList = List[OptionalSurface]

	CardList = List[Optional[ServerCard]]
	Grouped_Type = Dict[Suit: CardList]
	OptionalTrump = Tuple[Optional[ServerCard]]

	Position = Optional[Tuple[float, float]]
	DimensionTuple = Optional[Tuple[float, float]]
	OptionalSuit = Optional[Suit]
	SuitTuple = Tuple[OptionalSuit, OptionalSuit]

	PositionOrBlitsList = Union[Position, BlitsList]

	Colour = Sequence[int, int, int]
	OptionalColours = Optional[ColourScheme]

	NetworkFunction = Callable[[Server, *List[Any]], None]
	ConnectionAddress = Tuple[str, int]
	ConnectionDict = Dict[socket, ServerPlayer]

	RankType = Union[int, str]
	IndexOrKey = Union[int, str]
	NumberInput = Union[int, str]

	UpdaterDict = Dict[str: int]
	PlayerDict = Dict[str: Player]

	CardImageDict = Dict[str, Surface]
	TupledImageDict = Sequence[Tuple[str, Surface]]
	KeyTuple = Sequence[int]

	OptionalClientGame = Optional[ClientGame]
	OptionalDisplayManager = Optional[DisplayManager]
	OptionalClient = Optional[Client]

	ScoreboardText = Tuple[str, str]
	ScoreboardTextList = List[ScoreboardText]
	OptionalColourFader = Optional[ColourFader]
