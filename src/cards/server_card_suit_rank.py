from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum, IntEnum
from itertools import product

if TYPE_CHECKING:
    from src.special_knock_types import RankType

# Subclassing an Enum class means that it's automatically hashable.
# Subclassing IntEnum means that the __lt__, __gt__ & __eq__ methods are all filled in for us.
# Using the @unique decorator means that a __new__ method is automatically generated...
# ... ensuring that an existing instance is returned if one with those arguments has already been created.

# E.g. r = Rank(11)
# repr(r) = J
# str(r) = 'Jack'
# r.value = 11
# r < Rank(12) = True

RankMapper = {
        'J': 'Jack',
        'Q': 'Queen',
        'K': 'King',
        'A': 'Ace'
    }


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

    def __repr__(self):
        return str(self.value) if self.value < 11 else self.name

    def __str__(self):
        return str(self.value) if self.value < 11 else RankMapper[self.name]


Blacks = ('♣', '♠')

# Mixing in 'str' as a class means that we'll be able to sort Suit instances by value.


class Suit(str, Enum):
    Diamonds = '♢'
    Clubs = '♣'
    Spades = '♠'
    Hearts = '♡'

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.value

    def IsBlack(self):
        return self.value in Blacks

    def OtherOfColour(self):
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

    AllCardsList = []
    AllCardDict = {}

    def __new__(
            cls,
            rank: RankType,
            suit: str
    ):
        try:
            return cls.AllCardDict[(rank, suit)]
        except:
            new = super(ServerCard, cls).__new__(cls)
            cls.AllCardDict[(rank, suit)] = new
            cls.AllCardsList.append(new)
            return new

    def __init__(
            self,
            rank: RankType,
            suit: str
    ):

        self.Rank = Rank(rank)
        self.Suit = Suit(suit)
        self.ID = (rank, suit)
        self.PlayedBy = ''

    def AddToHand(self, playername: str):
        self.PlayedBy = playername
        return self

    def __str__(self):
        return f'{self.Rank} of {self.Suit}'

    def __repr__(self):
        return f'{self.Rank!r}{self.Suit!r}'
