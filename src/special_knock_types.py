from __future__ import annotations

from types import TracebackType

from typing import (
	List,
	Callable,
	Tuple,
	TYPE_CHECKING,
	Union,
	Optional,
	Sequence,
	Dict,
	Any,
	TypeVar,
	Iterable,
	Generator,
	NoReturn,
	Type
)

if not TYPE_CHECKING:
	raise Exception('Why are you doing this?? This module is only for type-checking!!!')

from pygame import Surface, Rect
from socket import socket
from itertools import cycle

from src.global_constants import Theme
from src.clientside_gameplay import ClientsideGameplay

from src.display.abstract_surfaces.knock_surface import KnockSurface
from src.display.abstract_surfaces.knock_surface_with_cards import CoverRect

from src.display.knock_surfaces.board_surf import BoardSurface
from src.display.knock_surfaces.game_surf import GameSurface
from src.display.knock_surfaces.scoreboard_surf import Scoreboard
from src.display.knock_surfaces.trump_card_surf import TrumpCardSurface

from src.display.abstract_text_rendering import FontAndLinesize
from src.display.display_manager import DisplayManager
from src.display.colours import ColourScheme
from src.display.faders import ColourFader
from src.display.mouse.mouse import Scrollwheel
from src.display.error_tracker import Errors
from src.display.input_context import InputContext

from src.players.players_abstract import Player, Hand
from src.players.players_server import ServerPlayer
from src.players.players_client import ClientPlayer, ClientHand

from src.network.network_server import Server
from src.network.network_client import Client

from src.game.server_game import ServerGame
from src.game.client_game import ClientGame
from src.cards.server_card_suit_rank import ServerCard, Suit, Rank
from src.cards.client_card import ClientCard

# noinspection PyProtectedMember,PyPackageRequirements
from Crypto.Cipher._mode_cbc import CbcMode as CipherType

OptionalRect = Optional[Rect]
RectList = List[OptionalRect]
CoverRectList = List[CoverRect]

OptionalSurface = Optional[Surface]
SurfaceList = List[Surface]

ServerCardList = List[ServerCard]
ClientCardList = List[ClientCard]
ServerCardDict = Dict[Tuple[Rank, Suit], ServerCard]
ClientCardDict = Dict[Tuple[Rank, Suit], ClientCard]
CardListTypeVar = TypeVar('CardListTypeVar', ServerCardList, ClientCardList)
Grouped_Type = Dict[Suit, CardListTypeVar]
OptionalTrump = Tuple[Optional[ServerCard]]
AnyCardList = List[Union[ServerCard, ClientCard]]

Position = Optional[Tuple[float, float]]
DimensionTuple = Optional[Tuple[float, float]]
OptionalSuit = Optional[Suit]
SuitTuple = Tuple[OptionalSuit, OptionalSuit]

Blittable = Optional[Tuple[Surface, Union[Rect, Position]]]
BlitsList = Union[List[Blittable], Sequence[Blittable]]
PositionOrBlitsList = Union[Position, BlitsList]
PositionSequence = Sequence[Tuple[float, float]]

Colour = Union[List[int], Tuple[int, int, int], Tuple[int, int, int, int]]
OptionalColours = Optional[ColourScheme]
ThemeTuple = Sequence[Theme]

NetworkFunction = Callable[[Server, *List[Any]], None]
ConnectionAddress = Tuple[str, int]
ConnectionDict = Dict[socket, ServerPlayer]
OptionalBytes = Optional[bytes]
OptionalCipherType = Optional[CipherType]
OptionalInt = Optional[int]
OptionalStr = Optional[str]

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

ArrowCursor = Sequence[str]
Cursor_Type = Tuple[DimensionTuple, Position, Sequence[int]]

OptionalFont = Optional[FontAndLinesize]
T = TypeVar('T')
IntOrBool = Union[int, bool]
GameParameters = Tuple[range, range, cycle]
EventsDictType = Dict[str, int]
PlayerNameList = List[str]
StringGenerator = Generator[str, None, None]
ClientStartUpReturnables = Tuple[Client, ClientsideGameplay, DisplayManager]
ServerStartUpReturnables = Tuple[Server, ServerGame, bool]
ServerUserInputsReturn = Tuple[int, str, str, bool]
ClientUpdateReturn = Tuple[Optional[str], bool]
AnyCardsIter = Iterable[CardListTypeVar]

ZoomReturnable = Tuple[int, bool]
ItMightReturn = Optional[NoReturn]

# TypeVars
CardTypeVar = TypeVar('CardTypeVar', bound=ServerCard)
KnockSurfaceTypeVar = TypeVar('KnockSurfaceTypeVar', bound=KnockSurface)
BoardSurfaceTypeVar = TypeVar('BoardSurfaceTypeVar', bound=BoardSurface)
GameSurfaceTypeVar = TypeVar('GameSurfaceTypeVar', bound=GameSurface)
ScoreboardSurfTypeVar = TypeVar('ScoreboardSurfTypeVar', bound=Scoreboard)
TrumpSurfTypeVar = TypeVar('TrumpSurfTypeVar', bound=TrumpCardSurface)
ColourSchemeTypeVar = TypeVar('ColourSchemeTypeVar', bound=ColourScheme)
DisplayManagerTypeVar = TypeVar('DisplayManagerTypeVar', bound=DisplayManager)
ErrorTrackerTypeVar = TypeVar('ErrorTrackerTypeVar', bound=Errors)
InputContextTypeVar = TypeVar('InputContextTypeVar', bound=InputContext)

# __exit__ types
ExitArg1 = Optional[Type[BaseException]]
ExitArg2 = Optional[BaseException]
ExitArg3 = Optional[TracebackType]
