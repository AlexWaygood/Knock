from typing import List, Tuple, TYPE_CHECKING, Union, Optional, Sequence, Dict

if TYPE_CHECKING:
	from pygame import Surface, Rect
	from src.Cards.ServerCard import ServerCard
	from src.Cards.Suit import Suit

	Blittable = Tuple[Surface, Rect]
	BlitsList = List[Optional[Blittable]]

	CardList = List[Optional[ServerCard]]
	Grouped_Type = Dict[Suit: CardList]

	Position = Tuple[float, float]
	SuitTuple = Tuple[Optional[Suit], Optional[Suit]]
	Colour = Sequence[int, int, int]

	RankType = Union[int, str]
	IndexOrKey = Union[int, str]
	NumberInput = Union[int, str]
