from __future__ import annotations

from typing import List, Callable, Tuple, TYPE_CHECKING, Union, Optional, Sequence, Dict, Any


if TYPE_CHECKING:
	from pygame import Surface, Rect
	from src.cards.server_card import ServerCard
	from src.cards.suit import Suit
	from src.network.server_class import Server
	from src.display.colour_scheme import ColourScheme

	Blittable = Optional[Tuple[Surface, Rect]]
	BlitsList = Union[List[Blittable], Sequence[Blittable]]

	CardList = List[Optional[ServerCard]]
	Grouped_Type = Dict[Suit: CardList]

	Position = Optional[Tuple[float, float]]
	SuitTuple = Tuple[Optional[Suit], Optional[Suit]]

	Colour = Sequence[int, int, int]
	OptionalColours = Optional[ColourScheme]

	NetworkFunction = Callable[[Server, *List[Any]], None]
	ConnectionAddress = Tuple[str, int]

	RankType = Union[int, str]
	IndexOrKey = Union[int, str]
	NumberInput = Union[int, str]
