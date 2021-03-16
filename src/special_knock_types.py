from __future__ import annotations

from typing import List, Callable, Tuple, TYPE_CHECKING, Union, Optional, Sequence, Dict, Any, Generator


if TYPE_CHECKING:
	from pygame import Surface, Rect
	from src.cards.server_card import ServerCard
	from src.cards.suit import Suit
	from src.network.server_class import Server
	from src.display.colour_scheme import ColourScheme
	from src.players.players_abstract import Player
	from src.display.abstract_surfaces.knock_surface_with_cards import CoverRect

	Blittable = Optional[Tuple[Surface, Rect]]
	BlitsList = Union[List[Blittable], Sequence[Blittable]]

	RectList = List[Optional[Rect]]
	CoverRectList = List[Optional[CoverRect]]
	SurfaceList = List[Optional[Surface]]

	CardList = List[Optional[ServerCard]]
	Grouped_Type = Dict[Suit: CardList]
	OptionalTrump = Tuple[Optional[ServerCard]]

	Position = Optional[Tuple[float, float]]
	DimensionTuple = Optional[Tuple[float, float]]
	SuitTuple = Tuple[Optional[Suit], Optional[Suit]]

	Colour = Sequence[int, int, int]
	OptionalColours = Optional[ColourScheme]

	NetworkFunction = Callable[[Server, *List[Any]], None]
	ConnectionAddress = Tuple[str, int]

	RankType = Union[int, str]
	IndexOrKey = Union[int, str]
	NumberInput = Union[int, str]

	ScoreboardGenerator = Generator[Tuple[str, str], None, None]

	UpdaterDict = Dict[str: int]
	PlayerDict = Dict[str: Player]

	CardImageDict = Dict[str, Surface]
	TupledImageDict = Sequence[Tuple[str, Surface]]
	KeyTuple = Tuple[int, ...]
