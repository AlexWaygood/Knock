"""An enumeration representing all possible card ranks in a standard French deck."""

from __future__ import annotations

from aenum import MultiValue, Unique

from typing import cast, TypeVar
from src import cached_readonly_property
import src.cards.card_typing_constants as tc
from src.cards.card_suit_rank_abc import SuitOrRankEnum, CardClassEnumMeta

# noinspection PyTypeChecker
R = TypeVar('R', bound='Rank')


class RankMeta(CardClassEnumMeta):
    """Metaclass for the `Rank` enum."""

    @cached_readonly_property
    def courtesan_ranks(cls: type[R], /) -> frozenset[R]:
        """Return a frozenset of the courtesan ranks."""
        return frozenset({cls.Jack, cls.Queen, cls.King, cls.Ace})

    @cached_readonly_property
    def non_courtesan_ranks(cls: type[R], /) -> frozenset[R]:
        """Return a frozenset of the non-courtesan ranks."""
        return frozenset(cls) - cls.courtesan_ranks

    def ranks_above(cls: type[R], n: tc.ALL_RANK_VALUES, /) -> frozenset[R]:
        """Return a frozenset of all the ranks above a certain value.

        Examples
        --------
        >>> len(Rank.ranks_above(10))
        4
        >>> Rank.ranks_above(12) == frozenset({Rank.King, Rank.Ace})
        True
        """
        return frozenset(rank for rank in cls if rank > Rank(n))

    def ranks_above_or_equal_to(cls: type[R], n: tc.ALL_RANK_VALUES, /) -> frozenset[R]:
        """Return a frozenset of all the ranks above or equal to a certain value.

        Examples
        --------
        >>> len(Rank.ranks_above_or_equal_to(10))
        5
        >>> Rank.ranks_above_or_equal_to(12) == frozenset({Rank.Queen, Rank.King, Rank.Ace})
        True
        """
        return frozenset(rank for rank in cls if rank >= Rank(n))

    def ranks_below(cls: type[R], n: tc.ALL_RANK_VALUES, /) -> frozenset[R]:
        """Return a frozenset of all the ranks below a certain value.

        Examples
        --------
        >>> len(Rank.ranks_below(4))
        2
        >>> Rank.ranks_below(4) == frozenset({Rank.Two, Rank.Three})
        True
        """
        return frozenset(rank for rank in cls if rank < Rank(n))

    def ranks_below_or_equal_to(cls: type[R], n: tc.ALL_RANK_VALUES) -> frozenset[R]:
        """Return a frozenset of all the ranks below or equal to a certain value.

        Examples
        --------
        >>> len(Rank.ranks_below_or_equal_to(4))
        3
        >>> Rank.ranks_below_or_equal_to(4) == frozenset({Rank.Two, Rank.Three, Rank.Four})
        True
        """
        return frozenset(rank for rank in cls if rank <= Rank(n))


class Rank(SuitOrRankEnum, metaclass=RankMeta, settings=(MultiValue, Unique)):
    # noinspection PyUnresolvedReferences
    """Enumeration representing all possible ranks a card could have.

    All `Rank` members have integer values between in range 2 <= x <= 14.
    They are comparable to other `Rank` members, but not to integers.

    Courtesan cards (Jack, Queen, King, Ace) are also accessible via the first letter of their name.

    Examples
    --------
    >>> Rank.Two == 2
    False
    >>> Rank.Ten > 5
    Traceback (most recent call last):
    TypeError: '>' not supported between instances of 'Rank' and 'int'
    >>> Rank(8) < Rank(14)
    True
    >>> Rank(3)
    Rank(3)
    >>> Rank(11)
    Rank(J)
    >>> Rank('J')
    Rank(J)
    """

    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Seven = 7
    Eight = 8
    Nine = 9
    Ten = 10
    Jack = 11, 'J'
    Queen = 12, 'Q'
    King = 13, 'K'
    Ace = 14, 'A'

    @cached_readonly_property
    def is_courtesan(self, /) -> bool:
        """Return `True` if the rank is one of `{Jack, Queen, King, Ace}` (the "courtesan ranks."), else `False`.

        Examples
        --------
        >>> Rank(10).is_courtesan
        False
        >>> Rank(11).is_courtesan
        True
        """

        return self in Rank.courtesan_ranks

    @cached_readonly_property
    def verbose_name(self, /) -> tc.ALL_RANK_VERBOSE_NAMES:
        """Return a verbose string representation of the Rank.

        Examples
        --------
        >>> Rank(10).verbose_name
        '10'
        >>> Rank(12).verbose_name
        'Queen'
        >>> print(f'{Rank(2):verbose}')
        2
        >>> f'{Rank(6):verbose}'
        '6'
        >>> print(f'{Rank(12):verbose}')
        Queen
        """

        verbose_name = self.name if self.is_courtesan else str(self.value)
        return cast(tc.ALL_RANK_VERBOSE_NAMES, verbose_name)

    @cached_readonly_property
    def concise_name(self, /) -> tc.ALL_RANK_CONCISE_NAMES:
        """Return a concise string representation of the Rank.

        Examples
        --------
        >>> Rank(10).concise_name
        '10'
        >>> Rank(14).concise_name
        'A'
        >>> f'{Rank(2):concise}'
        '2'
        >>> f'{Rank(14):concise}'
        'A'
        """

        concise_name = self.name[0] if self.is_courtesan else str(self.value)
        return cast(tc.ALL_RANK_CONCISE_NAMES, concise_name)

    @cached_readonly_property
    def rank_id(self, /) -> tc.ALL_RANK_IDS:
        # noinspection PyUnresolvedReferences
        """Return the 'ID' of the rank, which will be a `str` if the rank is courtesan, else an `int`.

        Examples
        --------
        >>> Rank(10).rank_id
        10
        >>> isinstance(_, int)
        True
        >>> Rank(13).rank_id
        'K'
        >>> isinstance(_, str)
        True
        """

        my_rank_id = self.concise_name if self.is_courtesan else self.value
        return cast(tc.ALL_RANK_IDS, my_rank_id)


if __name__ == '__main__':
    from doctest import testmod
    testmod()
