"""A function to sort the player's hand of cards, as well as several helper functions for achieving that end."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union, NamedTuple, Literal, cast, TypeVar
from src.cards import Suit, Rank
from itertools import groupby
from operator import attrgetter
from functools import partial

if TYPE_CHECKING:
	from src.cards.server_card import ServerCard
	from src.cards.client_card import ClientCard
	from src.players.players_client import HandSnapshotTuple

	# Pointless having this paramaterised with a TypeVar,
	# as it's never actually used in a situation where there are dependent types.
	AnyCardList = Union[list[ServerCard], list[ClientCard]]
	CardsGroupedBySuit = dict[Suit, AnyCardList]


FrozensetOfSuits = frozenset[Suit]
# noinspection PyTypeChecker
H = TypeVar('H', bound='HandInfoTuple')
# noinspection PyTypeChecker
S = TypeVar('S', bound='SuitOrderTuple')


def all_values_of_suit(cards_grouped_by_suits_dict: CardsGroupedBySuit, suit: Suit) -> list[Rank]:
	"""Given a certain suit, return a list of the ranks for each card in the player's hand of that suit.

	Parameters
	----------
	cards_grouped_by_suits_dict: `dict[Suit, list[Card]]`
		A dictionary mapping the suits in the hand to the cards in the hand that are of that suit.

	suit: Suit
		The suit for which the list of ranks is desired.

	Returns
	-------
	A list of `Rank` objects.
	"""

	return [card.rank for card in cards_grouped_by_suits_dict[suit]]


def max_of_colour(colour: FrozensetOfSuits, suits2cards_dict: CardsGroupedBySuit) -> Suit:
	"""Given a certain suit colour, return the suit for which there are higher-ranked cards in the hand.
	There are two suit colours (reds and blacks), and each suit colour has two suits corresponding to that colour.

	Parameters
	----------
	colour: `frozenset[Suit]`
		A frozenset of `Suit`s corresponding to a certain colour.

		This will be either the set of black suits (`frozenset({Suit.Clubs, Suit.Spades})`),
		or the set of red suits (`frozenset({Suit.Hearts, Suit.Diamonds})`),
		both of which are frozensets of length 2.

	suits2cards_dict: `dict[Suit, list[Card]]`
		A dictionary mapping the suits in the hand to the cards in the hand that are of that suit.

	Returns
	-------
	The suit of that colour for which there are higher-ranked cards in the hand.
	"""

	return max(filter(colour.__contains__, suits2cards_dict), key=partial(all_values_of_suit, suits2cards_dict))


def whichever_suit_present(colour: FrozensetOfSuits, cards_grouped_by_suits_dict: CardsGroupedBySuit) -> Suit:
	"""Given a colour, of which we know there is 1 suit in the hand, return whichever suit of that colour is present.

	Parameters
	----------
	colour: `frozenset[Suit]`
		A frozenset of `Suit`s corresponding to a certain colour.

		This will be either the set of black suits (`frozenset({Suit.Clubs, Suit.Spades})`),
		or the set of red suits (`frozenset({Suit.Hearts, Suit.Diamonds})`),
		both of which are frozensets of length 2.

	cards_grouped_by_suits_dict: `dict[Suit, list[Card]]`
		A dictionary mapping the suits in the hand to the cards in the hand that are of that suit.

	Returns
	-------
	A `Suit` object.
	"""

	return next(filter(cards_grouped_by_suits_dict.__contains__, colour))


def max_suit(cards_grouped_by_suits_dict: CardsGroupedBySuit) -> Suit:
	"""Return the suit for which there are the highest-ranked cards in the player's hand.

	Parameters
	----------
	cards_grouped_by_suits_dict: `dict[Suit, list[Card]]`
		A dictionary mapping the suits in the hand to the cards in the hand that are of that suit.

	Returns
	-------
	A `Suit` object.
	"""

	return max(cards_grouped_by_suits_dict, key=partial(all_values_of_suit, cards_grouped_by_suits_dict))


class HandInfoTuple(NamedTuple):
	"""A `NamedTuple` containing analysis of the player's hand.

	At index 0 in this tuple: a dictionary mapping the suits in the hand to the cards in the hand that are of that suit.
	And index 1: an integer representing the number of black suits in the player's hand.
	"""

	cards_grouped_by_suit_dict: CardsGroupedBySuit
	black_suits_present: Literal[0, 1, 2]

	@classmethod
	def from_hand(cls: type[H], hand: AnyCardList, /) -> H:
		"""Perform analysis on the player's hand, return the results of the analysis in the form of a `NamedTuple`.

		Parameters
		----------
		hand: list[Card]
			The player's hand.

		Returns
		-------
		An instance of the `HandInfoTuple` class.
		"""

		cards_grouped_by_suit_dict: CardsGroupedBySuit = {}
		black_suits_present = 0

		for k, g in groupby(hand, attrgetter('suit')):
			cards_grouped_by_suit_dict[k] = list(g)
			if k.is_black:
				black_suits_present += 1

		# noinspection PyArgumentList
		return cls(
			cards_grouped_by_suit_dict=cards_grouped_by_suit_dict,
			black_suits_present=cast(Literal[0, 1, 2], black_suits_present)
		)


def after_new_deal(*, hand: AnyCardList, trumpsuit: Suit) -> None:
	"""Sort a hand of cards in-place at the beginning of the round, following the pack being dealt.

	Parameters
	----------
	hand: `list`, a list of `Card` objects
		The hand to be sorted in-place.

	trumpsuit: `Suit`
		The trumpsuit for the current round.
	"""

	hand.sort(key=attrgetter('card_ID'), reverse=True)
	cards_grouped_by_suit_dict, black_suits_present = HandInfoTuple.from_hand(hand)

	sort_hand_part_two(
		hand=hand,
		cards_grouped_by_suit_dict=cards_grouped_by_suit_dict,
		trumpsuit=trumpsuit,
		black_suits_present=black_suits_present,
		after_card_play=False
	)


def after_playing_a_card(
		*,
		hand: AnyCardList,
		trumpsuit: Suit,
		played_suit: Suit,
		hand_snapshot: HandSnapshotTuple,
) -> None:
	"""Sort a hand of cards in-place after a card has been played.

	Parameters
	----------
	hand: `list`, a list of `Card` objects
		The hand to be sorted in-place.

	trumpsuit: `Suit`
		The trumpsuit for the current round.

	played_suit: `Suit`
		The suit that the player has just played.

	hand_snapshot: `HandSnapshotTuple`
		A `NamedTuple` representing a snapshot of a player's hand of cards immediately before playing a card.

		The specific information recorded is the suit of the first card in the player's hand,
		and the suit of the last card in the player's hand,
		at the moment before the playing of the card took place.
	"""

	if played_suit in hand_snapshot:
		return

	cards_grouped_by_suit_dict, black_suits_present = HandInfoTuple.from_hand(hand)

	if played_suit in cards_grouped_by_suit_dict:
		return

	sort_hand_part_two(
		hand=hand,
		cards_grouped_by_suit_dict=cards_grouped_by_suit_dict,
		trumpsuit=trumpsuit,
		black_suits_present=black_suits_present,
		after_card_play=True
	)


class SuitOrderTuple(NamedTuple):
	"""A `NamedTuple` indicating what the first and second suits should be in the sorted hand of cards.

	Parameters for alternative constructor classmethods
	(all of which return an instance of the class)
	---------------------------------------------------
	black_suits_present: `int`
		The number of black suits in the hand (could be 0, 1, or 2).

		This is not present as a parameter for the `from_hand_with_four_suits` constructor,
		as it is known that there will be two black suits present in a hand with four suits.

		It is present as a parameter for all other classmethod constructors.

	trumpsuit: `Suit`
		The trumpsuit for this round.

	trump_is_black: `bool`
		`True` if the trumpsuit this round is a black suit, else `False`.

	cards_grouped_by_suit_dict: `dict[Suit, list[Card]]`
		A dictionary mapping the suits the player holds in their hand
		to the cards in the player's hand that are of that suit.

	BLACKS: `frozenset[Suit]`
		A `frozenset` of the two black cards_grouped_by_suits_dict in the `Suit` enumeration.
		Included in the parameter list for optimisation reasons; essentially a global variable.

	REDS: `frozenset[Suit]`
		A `frozenset` of the two red cards_grouped_by_suits_dict in the `Suit` enumeration.
		Included in the parameter list for optimisation reasons; essentially a global variable.
	"""

	suit1: Suit
	suit2: Suit

	# noinspection PyPep8Naming
	@classmethod
	def from_hand_with_four_suits(
			cls: type[S],
			trumpsuit: Suit,
			trump_is_black: bool,
			cards_grouped_by_suit_dict: CardsGroupedBySuit,
			REDS: FrozensetOfSuits = Suit.REDS,
			BLACKS: FrozensetOfSuits = Suit.BLACKS
	) -> S:
		"""Given a hand with 2 suits, return a tuple indicating what the 1st & 2nd suits should be in the sorted hand.
		See class docstring for a full description of the parameters.
		"""

		suit1 = trumpsuit
		suit2 = max_of_colour((REDS if trump_is_black else BLACKS), cards_grouped_by_suit_dict)

		# noinspection PyArgumentList
		return cls(suit1=suit1, suit2=suit2)

	# noinspection PyPep8Naming
	@classmethod
	def from_hand_with_three_suits(
			cls: type[S],
			black_suits_present: Literal[1, 2],
			trumpsuit: Suit,
			trump_is_black: bool,
			cards_grouped_by_suit_dict: CardsGroupedBySuit,
			BLACKS: FrozensetOfSuits = Suit.BLACKS,
			REDS: FrozensetOfSuits = Suit.REDS
	) -> S:
		"""Given a hand with 3 suits, return a tuple indicating what the 1st & 2nd suits should be in the sorted hand.
		See class docstring for a full description of the parameters.
		"""

		# What we do if there are 2 black suits and one red suit in the hand
		if black_suits_present == 2:
			suit1 = trumpsuit if trump_is_black else max_of_colour(BLACKS, cards_grouped_by_suit_dict)
			suit2 = whichever_suit_present(REDS, cards_grouped_by_suit_dict)

		# What we do if there are 2 red suits and one black suit in the hand
		else:
			suit1 = max_of_colour(REDS, cards_grouped_by_suit_dict) if trump_is_black else trumpsuit
			suit2 = whichever_suit_present(BLACKS, cards_grouped_by_suit_dict)

		# noinspection PyArgumentList
		return cls(suit1=suit1, suit2=suit2)

	# noinspection PyPep8Naming
	@classmethod
	def from_hand_with_two_suits(
			cls: type[S],
			black_suits_present: Literal[0, 1, 2],
			trumpsuit: Suit,
			trump_is_black: bool,
			cards_grouped_by_suit_dict: CardsGroupedBySuit,
			REDS: FrozensetOfSuits = Suit.REDS,
			BLACKS: FrozensetOfSuits = Suit.BLACKS
	) -> S:
		"""Given a hand with 2 suits, return a tuple indicating what the 1st & 2nd suits should be in the sorted hand.
		See class docstring for a full description of the parameters.
		"""

		# What we do if all the cards in the hand are black
		if black_suits_present == 2:
			suit1 = trumpsuit if trump_is_black else max_suit(cards_grouped_by_suit_dict)
			# There are no red suits in the hand, so "suit2" is entirely arbitrary
			# It could be Suit.Hearts or Suit.Diamonds, either would do.
			suit2 = Suit.Hearts

		# What we do if some cards in the hand are black and some are red
		elif black_suits_present:
			if trumpsuit in cards_grouped_by_suit_dict:
				suit1 = trumpsuit
				suit2 = whichever_suit_present((REDS if trump_is_black else BLACKS), cards_grouped_by_suit_dict)
			else:
				suit1 = max_suit(cards_grouped_by_suit_dict)
				suit2 = next(filter(suit1.__ne__, cards_grouped_by_suit_dict))

		# What we do if all the cards in the hand are red
		else:
			suit1 = max_suit(cards_grouped_by_suit_dict) if trump_is_black else trumpsuit
			# There are no black suits in the hand, so "suit2" is entirely arbitrary
			# It could be Suit.Clubs or Suit.Spades, either would do.
			suit2 = Suit.Clubs

		# noinspection PyArgumentList
		return cls(suit1=suit1, suit2=suit2)


# noinspection PyPep8Naming
def sort_hand_part_two(
		*,
		hand: AnyCardList,
		cards_grouped_by_suit_dict: CardsGroupedBySuit,
		trumpsuit: Suit,
		black_suits_present: Literal[0, 1, 2],
		after_card_play: bool
) -> None:
	"""Sort a hand of cards in-place.

	Parameters
	----------
	hand: `list[Card]`
		A list of `Card` objects: the hand of cards to be sorted in-place.
		Could be a list of `ServerCard` or `ClientCard` objects; it makes no difference.

	cards_grouped_by_suit_dict: `dict[Suit, list[Card]]`
		A dictionary mapping the suits the player holds in their hand
		to the cards in the player's hand that are of that suit.

	trumpsuit: `Suit`
		The trumpsuit for the current round.

	black_suits_present: `int`
		The number of black suits in the player's hand (will be either 0, 1, or 2).

	after_card_play: `bool`
		`True` if the hand is being sorted immediately after a card being played.
		`False` if the hand is being sorted immediately after cards being dealt at the start of a new round.
	"""

	trump_is_black = trumpsuit.is_black

	if (suit_number := len(cards_grouped_by_suit_dict)) == 4:
		suit1, suit2 = SuitOrderTuple.from_hand_with_four_suits(
			trumpsuit=trumpsuit,
			trump_is_black=trump_is_black,
			cards_grouped_by_suit_dict=cards_grouped_by_suit_dict
		)

	elif suit_number == 3:
		suit1, suit2 = SuitOrderTuple.from_hand_with_three_suits(
			trumpsuit=trumpsuit,
			black_suits_present=black_suits_present,
			trump_is_black=trump_is_black,
			cards_grouped_by_suit_dict=cards_grouped_by_suit_dict
		)

	elif suit_number == 2:
		if after_card_play:
			return

		suit1, suit2 = SuitOrderTuple.from_hand_with_two_suits(
			trumpsuit=trumpsuit,
			black_suits_present=black_suits_present,
			trump_is_black=trump_is_black,
			cards_grouped_by_suit_dict=cards_grouped_by_suit_dict
		)

	else:
		return

	suit_dict = {
		suit1: 4,
		suit2: 3,
		suit1.other_of_colour: 2,
		suit2.other_of_colour: 1
	}

	hand.sort(key=lambda card: (suit_dict[card.suit], card.rank), reverse=True)
