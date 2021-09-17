from __future__ import annotations

from types import TracebackType

from typing import (
	Callable,
	TYPE_CHECKING,
	Union,
	Optional,
	Sequence,
	Any,
	TypeVar,
	Literal
)

if not TYPE_CHECKING:
	raise RuntimeError('Why are you doing this?? This module is only for type-checking!!!')

from pygame import Surface, Rect
from socket import socket

from src.static_constants import Theme

from src.display import (
	FontAndLinesize,
	DisplayManager,
	ColourScheme,
	ColourFader,
	Scrollwheel
)

from src.players import Player
from src.players.players_server import ServerPlayer
from src.players.players_client import ClientPlayer

from src.network.network_server import Server
from src.network.network_client import Client

from src.game.client_game import ClientGame
from src.cards import ServerCard, Suit
from src.cards.client_card import ClientCard

# noinspection PyProtectedMember,PyPackageRequirements
from Crypto.Cipher._mode_cbc import CbcMode as CipherType

OptionalTrump = tuple[Optional[ServerCard]]
AnyCardList = Union[list[ServerCard], list[ClientCard]]

Position = Optional[tuple[float, float]]
DimensionTuple = Optional[tuple[float, float]]
OptionalSuit = Optional[Suit]
SuitTuple = tuple[OptionalSuit, OptionalSuit]

Blittable = Optional[tuple[Surface, Union[Rect, Position]]]
BlitsList = Union[list[Blittable], Sequence[Blittable]]
PositionOrBlitsList = Union[Position, BlitsList]
PositionSequence = Sequence[tuple[float, float]]

Colour = Union[list[int], tuple[int, int, int], tuple[int, int, int, int]]
OptionalColours = Optional[ColourScheme]
ThemeTuple = Sequence[Theme]

NetworkFunction = Callable[[Server, list[Any]], None]
ConnectionAddress = tuple[str, int]
ConnectionDict = dict[socket, ServerPlayer]
OptionalBytes = Optional[bytes]
OptionalCipherType = Optional[CipherType]
OptionalInt = Optional[int]
OptionalStr = Optional[str]

RankType = Union[int, str]
StringOrInt = Union[int, str]
NumberInput = Union[int, str]

StringFontPositionList = list[tuple[str, FontAndLinesize, Position]]
ScoreboardTextArgsList = list[tuple[str, dict[str, Position]]]

UpdaterDict = dict[str, int]

PlayerList = list[Player]
ClientPlayerList = list[ClientPlayer]
ServerPlayerList = list[ServerPlayer]

PlayerDict = dict[str, Player]
ClientPlayerDict = dict[str, ClientPlayer]
ServerPlayerDict = dict[str, ServerPlayer]

CardImageDict = dict[str, Surface]
KeyTuple = Sequence[int]

OptionalClientGame = Optional[ClientGame]
OptionalDisplayManager = Optional[DisplayManager]
OptionalClient = Optional[Client]
OptionalScrollwheel = Optional[Scrollwheel]

ScoreboardText = tuple[str, str]
ScoreboardTextList = list[ScoreboardText]
OptionalColourFader = Optional[ColourFader]

ArrowCursor = Sequence[str]
Cursor_Type = tuple[DimensionTuple, Position, Sequence[int]]

OptionalFont = Optional[FontAndLinesize]
IntOrBool = Union[int, bool]
PlayerNameList = list[str]
ClientUpdateReturn = tuple[Optional[str], bool]

ZoomReturnable = tuple[int, bool]

PlayerTypeVar = TypeVar('PlayerTypeVar', bound=Player)

# __exit__ types
ExitArg1 = Optional[type[BaseException]]
ExitArg2 = Optional[BaseException]
ExitArg3 = Optional[TracebackType]
LiteralTrue = Literal[True]
