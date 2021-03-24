from __future__ import annotations
from typing import List, Callable, Tuple, TYPE_CHECKING, Union, Optional, Sequence, Dict, Any, TypeVar


if TYPE_CHECKING:
	from pygame import Surface, Rect
	from socket import socket

	from src.display.display_manager import DisplayManager
	from src.display.abstract_surfaces.knock_surface_with_cards import CoverRect
	from src.display.colours import ColourScheme
	from src.display.faders import ColourFader
	from src.display.mouse.mouse import Scrollwheel

	from src.players.players_abstract import Player, Hand
	from src.players.players_server import ServerPlayer
	from src.players.players_client import ClientPlayer, ClientHand

	from src.network.network_server import Server
	from src.network.network_client import Client

	from src.game.client_game import ClientGame
	from src.cards.server_card_suit_rank import ServerCard, Suit, Rank
	from src.cards.client_card import ClientCard

	Blittable = Optional[Tuple[Surface, Rect]]
	BlitsList = Union[List[Blittable], Sequence[Blittable]]

	OptionalRect = Optional[Rect]
	RectList = List[OptionalRect]
	CoverRectList = List[CoverRect]

	OptionalSurface = Optional[Surface]
	SurfaceList = List[Surface]

	ServerCardList = List[ServerCard]
	ServerCardDict = Dict[Tuple[Rank, Suit], ServerCard]
	CardListTypeVar = TypeVar('CardListTypeVar', ServerCardList, List[ClientCard])
	Grouped_Type = Dict[Suit, CardListTypeVar]
	OptionalTrump = Tuple[Optional[ServerCard]]
	AnyCardList = List[Union[ServerCard, ClientCard]]

	Position = Optional[Tuple[float, float]]
	DimensionTuple = Optional[Tuple[float, float]]
	OptionalSuit = Optional[Suit]
	SuitTuple = Tuple[OptionalSuit, OptionalSuit]

	PositionOrBlitsList = Union[Position, BlitsList]
	PositionList = List[Tuple[float, float]]

	Colour = Sequence[int, int, int]
	OptionalColours = Optional[ColourScheme]

	NetworkFunction = Callable[[Server, *List[Any]], None]
	ConnectionAddress = Tuple[str, int]
	ConnectionDict = Dict[socket, ServerPlayer]

	RankType = Union[int, str]
	StringOrInt = Union[int, str]
	NumberInput = Union[int, str]

	UpdaterDict = Dict[str, int]

	PlayerTypeVar = TypeVar('PlayerTypeVar', Player, ClientPlayer, ServerPlayer)

	PlayerList = List[Player]
	ClientPlayerList = List[ClientPlayer]
	ServerPlayerList = List[ServerPlayer]

	PlayerDict = Dict[str, Player]
	ClientPlayerDict = Dict[str, ClientPlayer]
	ServerPlayerDict = Dict[str, ServerPlayer]

	CardImageDict = Dict[str, Surface]
	TupledImageDict = Sequence[Tuple[str, Surface]]
	KeyTuple = Sequence[int]

	OptionalClientGame = Optional[ClientGame]
	OptionalDisplayManager = Optional[DisplayManager]
	OptionalClient = Optional[Client]
	OptionalScrollwheel = Optional[Scrollwheel]

	ScoreboardText = Tuple[str, str]
	ScoreboardTextList = List[ScoreboardText]
	OptionalColourFader = Optional[ColourFader]

	OptionalClientHand = Optional[ClientHand]
	AnyHand = Union[Hand, ClientHand]
	NumberList = List[int]
