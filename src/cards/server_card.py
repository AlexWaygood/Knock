"""An enumeration representing the serverside simulation of a pack of cards."""

from __future__ import annotations

from typing import TypeVar, TYPE_CHECKING
from src.cards.abstract_card import AbstractCard, next_card
from random import shuffle

if TYPE_CHECKING:
    # noinspection PyTypeChecker
    C = TypeVar('C', bound='ServerCard')


# noinspection PyTypeChecker
class ServerCard(AbstractCard):
    """An enumeration representing a pack of cards of the standard French deck (serverside version)."""

    @classmethod
    def randomly_shuffled(cls: type[C], /) -> list[C]:
        """Return a randomly shuffled copy of the pack, as a `list`.
        This is kept as a method, rather than a property, as it will return a different object every time.

        Examples
        --------
        >>> ServerPack.randomly_shuffled() is not ServerPack.randomly_shuffled()
        True
        >>> set(ServerPack.randomly_shuffled()) == set(ServerPack.randomly_shuffled()) == set(ServerPack)
        True
        """

        as_list = list(cls)
        shuffle(as_list)
        return as_list

    Two_of_Diamonds = next_card()
    Two_of_Clubs = next_card()
    Two_of_Spades = next_card()
    Two_of_Hearts = next_card()

    Three_of_Diamonds = next_card()
    Three_of_Clubs = next_card()
    Three_of_Spades = next_card()
    Three_of_Hearts = next_card()

    Four_of_Diamonds = next_card()
    Four_of_Clubs = next_card()
    Four_of_Spades = next_card()
    Four_of_Hearts = next_card()

    Five_of_Diamonds = next_card()
    Five_of_Clubs = next_card()
    Five_of_Spades = next_card()
    Five_of_Hearts = next_card()

    Six_of_Diamonds = next_card()
    Six_of_Clubs = next_card()
    Six_of_Spades = next_card()
    Six_of_Hearts = next_card()

    Seven_of_Diamonds = next_card()
    Seven_of_Clubs = next_card()
    Seven_of_Spades = next_card()
    Seven_of_Hearts = next_card()

    Eight_of_Diamonds = next_card()
    Eight_of_Clubs = next_card()
    Eight_of_Spades = next_card()
    Eight_of_Hearts = next_card()

    Nine_of_Diamonds = next_card()
    Nine_of_Clubs = next_card()
    Nine_of_Spades = next_card()
    Nine_of_Hearts = next_card()

    Ten_of_Diamonds = next_card()
    Ten_of_Clubs = next_card()
    Ten_of_Spades = next_card()
    Ten_of_Hearts = next_card()

    Jack_of_Diamonds = next_card()
    Jack_of_Clubs = next_card()
    Jack_of_Spades = next_card()
    Jack_of_Hearts = next_card()

    Queen_of_Diamonds = next_card()
    Queen_of_Clubs = next_card()
    Queen_of_Spades = next_card()
    Queen_of_Hearts = next_card()

    King_of_Diamonds = next_card()
    King_of_Clubs = next_card()
    King_of_Spades = next_card()
    King_of_Hearts = next_card()

    Ace_of_Diamonds = next_card()
    Ace_of_Clubs = next_card()
    Ace_of_Spades = next_card()
    Ace_of_Hearts = next_card()


# An alias for the Enum just defined above, so that we can do, e.g., `ServerPack.BLACKS` in other modules.
ServerPack = ServerCard
