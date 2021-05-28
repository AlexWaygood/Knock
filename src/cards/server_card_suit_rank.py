from __future__ import annotations
from typing import TYPE_CHECKING, Type
from enum import Enum, IntEnum
from itertools import product

if TYPE_CHECKING:
    from src.special_knock_types import CardTypeVar, RankType, ServerCardList, ServerCardDict


# Two card-related global constants

RANK_MAPPER = {
        'J': 'Jack',
        'Q': 'Queen',
        'K': 'King',
        'A': 'Ace'
    }

BLACKS = ('♣', '♠')

# Subclassing an Enum class means that it's automatically hashable.
# Subclassing IntEnum means that the __lt__, __gt__ & __eq__ methods are all filled in for us.

# E.g. r = Rank(11)
# repr(r) = J
# str(r) = 'Jack'
# r.value = 11
# r < Rank(12) = True


class Rank(IntEnum):
    N2 = 2
    N3 = 3
    N4 = 4
    N5 = 5
    N6 = 6
    N7 = 7
    N8 = 8
    N9 = 9
    N10 = 10
    J = 11
    Q = 12
    K = 13
    A = 14

    def __repr__(self) -> str:
        return str(self.value) if self.value < 11 else self.name

    def __str__(self) -> str:
        return str(self.value) if self.value < 11 else RANK_MAPPER[self.name]


class Suit(str, Enum):  # Mixing in 'str' as a class means that we'll be able to sort Suit instances by value.
    Diamonds = '♢'
    Clubs = '♣'
    Spades = '♠'
    Hearts = '♡'

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.value

    def IsBlack(self) -> bool:
        return self.value in BLACKS

    def OtherOfColour(self) -> Suit:
        if self.IsBlack():
            return Suit('♣' if repr(self) == '♠' else '♠')
        return Suit('♢' if repr(self) == '♡' else '♡')


# Imported by both the ServerGame and ClientGame scripts
AllCardValues = list(product(Rank, Suit))

# Imported by the ClientCard script
AllCardIDs = [f'{ID[0]!r}{ID[1]!r}' for ID in AllCardValues]


class ServerCard:
    """Class representing a playing card from a standard deck (excluding jokers)"""
    __slots__ = 'Rank', 'Suit', 'PlayedBy', 'ID'

    AllCardsList: ServerCardList = []
    AllCardDict: ServerCardDict = {}

    def __new__(
            cls: Type[CardTypeVar],
            rank: RankType,
            suit: str
    ) -> CardTypeVar:

        key = (Rank(rank), Suit(suit))

        try:
            return cls.AllCardDict[key]
        except KeyError:
            new = super(ServerCard, cls).__new__(cls)
            cls.AllCardDict[key] = new
            return new

    def __init__(
            self,
            rank: RankType,
            suit: str
    ):
        self.Rank = Rank(rank)
        self.Suit = Suit(suit)
        self.ID = (self.Rank, self.Suit)
        self.PlayedBy = ''

    @classmethod
    def MakePack(cls) -> None:
        cls.AllCardsList = [cls(*value) for value in AllCardValues]

    def AddToHand(self: CardTypeVar, playername: str) -> CardTypeVar:
        self.PlayedBy = playername
        return self

    def __str__(self) -> str:
        return f'{self.Rank} of {self.Suit}'

    def __repr__(self) -> str:
        return f'{self.Rank!r}{self.Suit!r}'
