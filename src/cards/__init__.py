"""All classes and functions relating to the implementation of a pack of cards.

`ServerCard` and `ClientCard` are not imported here, as the one has serverside-specific implementation details,
and the other has clientside-specific implementation details.
"""

from src.cards.rank import Rank
from src.cards.suit import Suit

if __name__ == '__main__':
	from doctest import testmod
	from src.cards import rank, suit, server_card, client_card, card_suit_rank_abc, abstract_card, card_typing_constants

	for module in (rank, suit, server_card, client_card, abstract_card, card_typing_constants, card_suit_rank_abc):
		# noinspection PyTypeChecker
		testmod(module)
