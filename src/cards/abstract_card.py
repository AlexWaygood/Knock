"""An 'abstract card' class that is used as a base class by the `ClientCard` and `ServerCard` classes.
Also in this module is a metaclass to support that class, and an `iter_pack` function to support iterating .
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Literal, TypeVar, cast, Union, Any, Callable, Iterator, NamedTuple, overload, NoReturn
from itertools import product, cycle

from aenum import skip, MultiValue, Unique

from src import cached_readonly_property
from src.cards.card_suit_rank_abc import CardClassEnumMeta, CardClassEnum
from src.cards.suit import Suit
from src.cards.rank import Rank
import src.cards.card_typing_constants as tc

if TYPE_CHECKING:
    from src.special_knock_types import ExitArg1, ExitArg2, ExitArg3

SuitQueryType = Union[Suit, tc.SUIT_NAMES, tc.ALL_SUIT_VALUES]

RankQueryType = Union[
    Rank,
    tc.ALL_RANK_VALUES,
    tc.ALL_RANK_CONCISE_NAMES,
    tc.ALL_RANK_VERBOSE_NAMES,
    tc.NON_COURTESAN_RANKS
]

# noinspection PyTypeChecker
CE = TypeVar('CE', bound='CardEnumMeta')

# noinspection PyTypeChecker
C = TypeVar('C', bound='AbstractCardBase')


# noinspection PyPropertyDefinition,PyMethodParameters,PyPep8Naming
class CardEnumMeta(CardClassEnumMeta):
    """Metaclass for the `Card` enums."""

    def __enter__(cls: CE) -> CE:
        """Return `cls`, enabling the use of a `Pack` object as a context manager.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> with ServerPack as P:
        ...     print(P.Ace_of_Spades)
        ...
        ServerCard(A♠)
        """

        return cls

    def __exit__(cls, exc_type: ExitArg1, exc_val: ExitArg2, exc_tb: ExitArg3) -> None:
        pass

    # Seven methods and properties for accessing cards by rank ###

    def cards_of_rank(cls: type[C], n: tc.ALL_RANK_VALUES, /) -> frozenset[C]:
        # noinspection PyUnresolvedReferences
        """Return a frozenset of all cards of rank `n`.

        Example
        -------
        >>> from src.cards.server_card import ServerPack
        >>> with ServerPack as P:
        ...     P.cards_of_rank(2) == frozenset({P.Two_of_Clubs, P.Two_of_Hearts, P.Two_of_Diamonds, P.Two_of_Spades})
        ...
        True
        >>> with ServerPack as P:
        ...     P.cards_of_rank(14) == frozenset({P.Ace_of_Hearts, P.Ace_of_Spades, P.Ace_of_Clubs, P.Ace_of_Diamonds})
        ...
        True
        """

        return frozenset(card for card in cls if card.rank == Rank(n))

    def cards_with_rank_above(cls: type[C], n: tc.ALL_RANK_VALUES, /) -> frozenset[C]:
        # noinspection PyUnresolvedReferences
        """Return a frozenset of all cards with rank > `n`.

        Example
        -------
        >>> from src.cards.server_card import ServerPack
        >>> greater_than_4 = ServerPack.cards_with_rank_above(4)
        >>> all(card.rank > Rank(4) for card in greater_than_4)
        True
        >>> len(greater_than_4)
        40
        """

        return frozenset(card for card in cls if card.rank > Rank(n))

    def cards_with_rank_above_or_equal_to(cls: type[C], n: tc.ALL_RANK_VALUES, /) -> frozenset[C]:
        # noinspection PyUnresolvedReferences
        """Return a frozenset of all cards with rank >= `n`.

        Example
        -------
        >>> from src.cards.server_card import ServerPack
        >>> ge_2 = ServerPack.cards_with_rank_above_or_equal_to(2)
        >>> all(card.rank >= Rank(2) for card in ge_2)
        True
        >>> len(ge_2)
        52
        """

        return frozenset(card for card in cls if card.rank >= Rank(n))

    def cards_with_rank_below(cls: type[C], n: tc.ALL_RANK_VALUES, /) -> frozenset[C]:
        # noinspection PyUnresolvedReferences
        """Return a frozenset of all cards with rank < `n`.

        Example
        -------
        >>> from src.cards.server_card import ServerPack
        >>> less_than_11 = ServerPack.cards_with_rank_below(11)
        >>> all(card.rank < Rank(11) for card in less_than_11)
        True
        >>> len(less_than_11)
        36
        """

        return frozenset(card for card in cls if card.rank < Rank(n))

    def cards_with_rank_below_or_equal_to(cls: type[C], n: tc.ALL_RANK_VALUES, /) -> frozenset[C]:
        # noinspection PyUnresolvedReferences
        """Return a frozenset of all cards with rank <= `n`.

        Example
        -------
        >>> from src.cards.server_card import ServerPack
        >>> le_8 = ServerPack.cards_with_rank_below_or_equal_to(8)
        >>> all(card.rank <= Rank(8) for card in le_8)
        True
        >>> len(le_8)
        28
        """
        return frozenset(card for card in cls if card.rank <= Rank(n))

    @cached_readonly_property
    def courtesan_cards(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a `frozenset` of all the courtesan cards in the pack.
        The "courtesan cards" are the Jacks, Queens, Kings and Aces.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> len(ServerPack.courtesan_cards)
        16
        >>> ServerPack.Queen_of_Clubs in ServerPack.courtesan_cards
        True
        >>> ServerPack.Three_of_Diamonds in ServerPack.courtesan_cards
        False
        >>> ServerPack.courtesan_cards is ServerPack.courtesan_cards
        True
        """

        return cls.cards_with_rank_above(10)

    @cached_readonly_property
    def non_courtesan_cards(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a `frozenset` of all the non-courtesan cards in the pack.
        The "courtesan cards" are the Jacks, Queens, Kings and Aces.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> len(ServerPack.non_courtesan_cards)
        36
        >>> ServerPack.Queen_of_Clubs in ServerPack.non_courtesan_cards
        False
        >>> ServerPack.Three_of_Diamonds in ServerPack.non_courtesan_cards
        True
        >>> ServerPack.non_courtesan_cards is ServerPack.non_courtesan_cards
        True
        """

        return cls.cards_with_rank_below(11)

    # Four properties for accessing cards by suit ###

    @cached_readonly_property
    def HEARTS(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a frozenset of all cards that are hearts.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> all(card.suit is Suit.Hearts for card in ServerPack.HEARTS)
        True
        """
        return frozenset(filter(lambda card: card.suit is Suit.Hearts, cls))

    @cached_readonly_property
    def CLUBS(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a frozenset of all cards that are clubs

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> all(card.suit is Suit.Clubs for card in ServerPack.CLUBS)
        True
        >>> len(ServerPack.CLUBS)
        13
        """
        return frozenset(filter(lambda card: card.suit is Suit.Clubs, cls))

    @cached_readonly_property
    def SPADES(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a frozenset of all cards that are spades.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> all(card.suit is Suit.Spades for card in ServerPack.SPADES)
        True
        >>> len(ServerPack.SPADES)
        13
        """
        return frozenset(filter(lambda card: card.suit is Suit.Spades, cls))

    @cached_readonly_property
    def DIAMONDS(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a frozenset of all cards that are diamonds.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> all(card.suit is Suit.Diamonds for card in ServerPack.DIAMONDS)
        True
        >>> len(ServerPack.DIAMONDS)
        13
        """
        return frozenset(filter(lambda card: card.suit is Suit.Diamonds, cls))

    # Two classmethod properties for accessing cards by colour ###

    @cached_readonly_property
    def REDS(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a frozenset of all the red cards

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> all(card.is_red for card in ServerPack.REDS)
        True
        >>> len(ServerPack.REDS)
        26
        """
        return cls.DIAMONDS | cls.HEARTS

    @cached_readonly_property
    def BLACKS(cls: type[C], /) -> frozenset[C]:
        # noinspection PyTypeChecker,PyUnresolvedReferences
        """Return a frozenset of all the black cards.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> all(card.is_black for card in ServerPack.BLACKS)
        True
        >>> len(ServerPack.BLACKS)
        26
        """
        return cls.CLUBS | cls.SPADES

    def card_with_pack_index(cls: type[C], i: int, /) -> C:
        """Return the card in the pack with a certain index.
        This method is used for serialising and deserialising cards in communications between the server & client.
        """

        return cls._all_cards[i]


RankIDType, SuitIDType = tc.ALL_RANK_IDS, tc.ALL_SUIT_VALUES
StringIDType, TupleIDType = tc.ALL_CARD_STRING_IDS, tc.ALL_CARD_TUPLE_IDS
# noinspection PyTypeChecker
CEC = TypeVar('CEC', bound='CardEnumConstructor')


class CardEnumConstructor(NamedTuple):
    """All the arguments needed for construction of a Card enum member.

    Each item in the below-defined tuple corresponds to a way the member
    can be programmatically accessed from the Enum.
    """

    value: tuple[Rank, Suit]
    string_id: StringIDType
    tuple_id: TupleIDType
    rank_and_suit_id: tuple[Rank, SuitIDType]
    rank_id_and_suit: tuple[RankIDType, Suit]

    @classmethod
    def construct_pack(cls: type[CEC], /) -> Iterator[CEC]:
        """Iterate through all possible combinations of rank and suit."""

        for rank, suit in product(Rank, Suit):
            # noinspection PyArgumentList
            yield cls(
                value=(rank, suit),
                string_id=f'{rank:concise}{suit:concise}',
                tuple_id=(rank.rank_id, suit.value),
                rank_and_suit_id=(rank, suit.value),
                rank_id_and_suit=(rank.rank_id, suit)
            )

    @classmethod
    def cycle_through_pack(cls: type[CEC], /) -> Iterator[CEC]:
        """Cycle endlessly through all possible combinations of rank and suit."""
        return cycle(tuple(cls.construct_pack()))


GetNextCardFunc = Callable[[], CardEnumConstructor]
next_card: GetNextCardFunc = CardEnumConstructor.cycle_through_pack().__next__


class AbstractCard(CardClassEnum, metaclass=CardEnumMeta, settings=(MultiValue, Unique)):
    # noinspection PyUnresolvedReferences
    """Base class for `ServerCard` and `ClientCard`.

    All `Card` Enums have values of (<Rank>, <Suit>) tuples.
    However, they can be looked up in multiple ways.

    Examples
    --------
    >>> from src.cards.server_card import ServerCard
    >>> (
    ... ServerCard('10♠')
    ... is ServerCard((10, '♠'))
    ... is ServerCard((Rank(10), Suit('♠')))
    ... is ServerCard((Rank(10), '♠'))
    ... is ServerCard((10, Suit('♠')))
    ... is ServerCard.Ten_of_Spades
    ... is ServerCard(ServerCard.Ten_of_Spades)
    ... )
    True
    >>> ServerCard('7♣')
    ServerCard(7♣)
    >>> ServerCard('Q♠')
    ServerCard(Q♠)
    """

    _all_cards = skip([])

    def __init__(self, *args: Any) -> None:
        self._all_cards.append(self)

    # Several properties to make this tuple a bit more NamedTuple-ish.

    @cached_readonly_property
    def rank(self, /) -> Rank:
        # noinspection PyUnresolvedReferences
        """Return the rank of the card, a member of the `Rank` enum.

         Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> ServerPack.Two_of_Clubs.rank is Rank.Two
        True
        >>> ServerPack.Ace_of_Hearts.rank is ServerPack.Ace_of_Spades.rank is Rank.Ace
        True
        """
        return self.value[0]

    # noinspection PyTypeChecker
    @cached_readonly_property
    def suit(self, /) -> Suit:
        """Return the suit of the card, a member of the `Suit` enum.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> ServerPack.Queen_of_Clubs.suit is Suit.Clubs
        True
        """
        return self.value[1]

    def __iter__(self) -> Iterator[Union[Rank, Suit]]:
        # noinspection PyUnresolvedReferences
        """If a card is conceived of as a (<rank>, <suit>) tuple, iterate through members of that tuple.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> tuple(ServerPack.Eight_of_Spades) == ServerPack.Eight_of_Spades.value == (Rank(8), Suit('♠'))
        True
        >>> for item in ServerPack.Five_of_Hearts:
        ...     print(item)
        ...
        Rank(5)
        Suit(♡)
        """
        return iter(self.value)

    @overload
    def __getitem__(self, item: Literal[0]) -> Rank: ...

    @overload
    def __getitem__(self, item: Literal[1]) -> Suit: ...

    def __getitem__(self, item: int) -> Union[Rank, Suit]:
        # noinspection PyUnresolvedReferences
        """If a card is conceived of as a (<rank>, <suit>) tuple, access members of that tuple by index.

        Examples
        --------
        >>> from src.cards.server_card import ServerPack
        >>> ServerPack.Three_of_Diamonds[0] is Rank(3)
        True
        >>> ServerPack.Seven_of_Clubs[1] is Suit.Clubs
        True
        """

        return self.value[item]

    @cached_readonly_property
    def index_in_pack(self, /) -> int:
        """Get the index of this card relative to the list of all cards, an integer in range 0 <= x <= 51.
        This property is used for serialising and deserialising cards in messages between the server and the client.
        """

        return self._all_cards.index(self)

    def is_of_rank(self, rank_arg: RankQueryType) -> bool:
        """Return `True` if the card is of a certain rank, else `False`. A rank may be identified by name or value."""

        try:
            rank = Rank(rank_arg)
        except ValueError as err:
            try:
                rank = Rank[rank_arg]
            except KeyError:
                try:
                    rank = next(r for r in Rank if rank_arg in {r.concise_name, r.verbose_name})
                except StopIteration:
                    raise err from None

        return self.rank is rank

    def is_of_suit(self, suit_arg: SuitQueryType) -> bool:
        """Return `True` if the card is of a certain suit, else `False`. A suit may be identified by name or value."""

        try:
            suit = Suit(suit_arg)
        except ValueError as err:
            try:
                suit = Suit[suit_arg]
            except KeyError:
                raise err from None

        return self.suit is suit

    # Some other properties that give us some other means of identifying the card.
    @cached_readonly_property
    def verbose_name(self, /) -> tc.ALL_CARD_NAMES:
        """Get the name of a card, a string.

        Examples
        --------
        >>> from src.cards.server_card import ServerCard
        >>> ServerCard('A♡').verbose_name
        'Ace of Hearts'
        """
        # We have to call this card_name so the name of the method doesn't clash with the enum `.name` attribute.
        name = f'{self.rank:verbose} of {self.suit:verbose}'
        return cast(tc.ALL_CARD_NAMES, name)

    @cached_readonly_property
    def concise_name(self, /) -> tc.ALL_CARD_STRING_IDS:
        """Return the 'string_ID' of a card.

        Examples
        --------
        >>> from src.cards.server_card import ServerCard
        >>> ServerCard.Jack_of_Hearts.concise_name
        'J♡'
        """

        concise_name = f'{self.rank:concise}{self.suit:concise}'
        return cast(tc.ALL_CARD_STRING_IDS, concise_name)

    @cached_readonly_property
    def tuple_id(self, /) -> tc.ALL_CARD_TUPLE_IDS:
        # noinspection PyUnresolvedReferences
        """Return the `tuple_ID` of a card.

        Can be an (<int>, <int>) tuple or a (<str>, <str>) tuple,
        depending on whether the card is a courtesan card or not.

        Examples
        --------
        >>> from src.cards.server_card import ServerCard
        >>> # The five of spades is a number card, not a courtesan card.
        >>> card_id1 = ServerCard.Five_of_Spades.tuple_id
        >>> card_id1
        (5, '♠')
        >>> type(card_id1[0])
        <class 'int'>
        >>> type(card_id1[1])
        <class 'str'>
        >>> # The King of Clubs is a courtesan card.
        >>> card_id2 = ServerCard.King_of_Clubs.tuple_id
        >>> card_id2
        ('K', '♣')
        >>> type(card_id2[0])
        <class 'str'>
        >>> type(card_id2[1])
        <class 'str'>
        """

        tuple_id = self.rank.rank_id, self.suit.value
        return cast(tc.ALL_CARD_TUPLE_IDS, tuple_id)

    # Some properties that gives us some other information about the card.

    @cached_readonly_property
    def is_courtesan_card(self, /) -> bool:
        """Return `True` if the rank is one of `{Jack, Queen, King, Ace}` (the "courtesan cards"), else `False"""
        return self.rank.is_courtesan

    @cached_readonly_property
    def is_black(self, /) -> bool:
        """Return `True` if the card is black, else `False`"""
        return self.suit.is_black

    @cached_readonly_property
    def is_red(self, /) -> bool:
        """Return `True` if the card is red, else `False`"""
        return self.suit.is_red

    # Context-manager methods.

    def __enter__(self: C) -> C:
        """`Card` objects can be used as a context manager.

        Examples
        --------
        >>> from src.cards.server_card import ServerCard
        >>> with ServerCard('Q♠') as s:
        ...     s == ServerCard.Queen_of_Spades
        ...
        True
        """

        return self

    def __exit__(self, exc_type: ExitArg1, exc_val: ExitArg2, exc_tb: ExitArg3) -> None:
        pass

    # Some methods to give us better exception messages if somebody tries to directly compare two cards together.

    @property
    def __comparison_exception_message(self, /) -> str:
        return 'Two cards cannot be compared without knowing the trumpsuit for the round.'

    def __gt__(self, other: Any) -> NoReturn:
        if type(other) is type(self):
            raise TypeError(self.__comparison_exception_message)
        return super().__gt__(other)

    def __ge__(self, other: Any) -> NoReturn:
        if type(other) is type(self):
            raise TypeError(self.__comparison_exception_message)
        return super().__ge__(other)

    def __lt__(self, other: Any) -> NoReturn:
        if type(other) is type(self):
            raise TypeError(self.__comparison_exception_message)
        return super().__lt__(other)

    def __le__(self, other: Any) -> NoReturn:
        if type(other) is type(self):
            raise TypeError(self.__comparison_exception_message)
        return super().__le__(other)


if __name__ == '__main__':
    from doctest import testmod
    testmod()
