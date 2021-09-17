"""Several verbose constants that are only used for type-hinting purposes,
but need to be available at runtime for the `typing.cast` function."""

from typing import Literal

ALL_STRING_IDS_AS_TUPLE = tuple[
    Literal['10♠'], Literal['2♡'], Literal['7♢'], Literal['J♡'], Literal['6♢'], Literal['4♣'], Literal['8♣'],
    Literal['10♡'], Literal['2♣'], Literal['A♠'], Literal['3♢'], Literal['K♡'], Literal['2♠'], Literal['7♡'],
    Literal['K♠'], Literal['4♠'], Literal['6♡'], Literal['q♣'], Literal['A♢'], Literal['3♣'], Literal['5♣'],
    Literal['10♣'], Literal['2♢'], Literal['8♠'], Literal['4♢'], Literal['A♣'], Literal['5♢'], Literal['K♢'],
    Literal['8♡'], Literal['9♣'], Literal['9♡'], Literal['5♠'], Literal['4♡'], Literal['K♣'], Literal['5♡'],
    Literal['q♢'], Literal['7♣'], Literal['J♠'], Literal['9♠'], Literal['q♠'], Literal['3♠'], Literal['7♠'],
    Literal['6♠'], Literal['J♣'], Literal['9♢'], Literal['3♡'], Literal['J♢'], Literal['q♡'], Literal['8♢'],
    Literal['A♡'], Literal['6♣'], Literal['10♢']
]

ALL_SUIT_VALUES = Literal['♢', '♣', '♠', '♡']
ALL_RANK_VERBOSE_NAMES = Literal['2', '3', '4', '5', '6', '7', '8', '9', '10', 'Jack', 'Queen', 'King', 'Ace']
ALL_RANK_CONCISE_NAMES = Literal['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
ALL_RANK_IDS = Literal[2, 3, 4, 5, 6, 7, 8, 9, 10, 'J', 'Q', 'K', 'A']
ALL_RANK_VALUES = Literal[2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]

ALL_CARD_STRING_IDS = Literal[
    '10♠', '2♡', '7♢', 'J♡', '6♢', '4♣', '8♣', '10♡', '2♣', 'A♠', '3♢', 'K♡', '2♠', '7♡', 'K♠', '4♠', '6♡', 'q♣',
    'A♢', '3♣', '5♣', '10♣', '2♢', '8♠', '4♢', 'A♣', '5♢', 'K♢', '8♡', '9♣', '9♡', '5♠', '4♡', 'K♣', '5♡', 'q♢',
    '7♣', 'J♠', '9♠', 'q♠', '3♠', '7♠', '6♠', 'J♣', '9♢', '3♡', 'J♢', 'q♡', '8♢', 'A♡', '6♣', '10♢'
]


ALL_CARD_TUPLE_IDS = tuple[ALL_RANK_IDS, ALL_SUIT_VALUES]


ALL_CARD_NAMES = Literal[
    '2 of Diamonds', '2 of Clubs', '2 of Spades', '2 of Hearts', '3 of Diamonds', '3 of Clubs', '3 of Spades',
    '3 of Hearts', '4 of Diamonds', '4 of Clubs', '4 of Spades', '4 of Hearts', '5 of Diamonds', '5 of Clubs',
    '5 of Spades', '5 of Hearts', '6 of Diamonds', '6 of Clubs', '6 of Spades', '6 of Hearts', '7 of Diamonds',
    '7 of Clubs', '7 of Spades', '7 of Hearts', '8 of Diamonds', '8 of Clubs', '8 of Spades', '8 of Hearts',
    '9 of Diamonds', '9 of Clubs', '9 of Spades', '9 of Hearts', '10 of Diamonds', '10 of Clubs', '10 of Spades',
    '10 of Hearts', 'Jack of Diamonds', 'Jack of Clubs', 'Jack of Spades', 'Jack of Hearts', 'Queen of Diamonds',
    'Queen of Clubs', 'Queen of Spades', 'Queen of Hearts', 'King of Diamonds', 'King of Clubs', 'King of Spades',
    'King of Hearts', 'Ace of Diamonds', 'Ace of Clubs', 'Ace of Spades', 'Ace of Hearts'
]

PossibleWinValues = Literal[
    0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27
]

NON_COURTESAN_RANKS = Literal['Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten']
SUIT_NAMES = Literal['Diamond', 'Clubs', 'Spades', 'Hearts']
