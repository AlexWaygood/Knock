from __future__ import annotations
from typing import List, Callable, Tuple, TYPE_CHECKING, Union, Optional, Sequence, Dict, Any, Generator


if TYPE_CHECKING:
	from pygame import Surface, Rect
	from socket import socket

	from src.display.abstract_surfaces.knock_surface_with_cards import CoverRect
	from src.display.colours import ColourScheme

	from src.players.players_abstract import Player
	from src.players.players_server import ServerPlayer

	from src.cards.server_card_suit_rank import ServerCard, Suit
	from src.network.netw_server import Server

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
	SuitTuple = Tuple[Optional[Suit], Optional[Suit]]

	PositionOrBlitsList = Union[Position, BlitsList]

	Colour = Sequence[int, int, int]
	OptionalColours = Optional[ColourScheme]

	NetworkFunction = Callable[[Server, *List[Any]], None]
	ConnectionAddress = Tuple[str, int]
	ConnectionDict = Dict[socket, ServerPlayer]

	RankType = Union[int, str]
	IndexOrKey = Union[int, str]
	NumberInput = Union[int, str]

	ScoreboardGenerator = Generator[Tuple[str, str], None, None]

	UpdaterDict = Dict[str: int]
	PlayerDict = Dict[str: Player]

	CardImageDict = Dict[str, Surface]
	TupledImageDict = Sequence[Tuple[str, Surface]]
	KeyTuple = Sequence[int]
