from __future__ import annotations

from typing import TYPE_CHECKING, List
from src.cards.server_card_suit_rank import Suit, Rank
from itertools import groupby
from operator import attrgetter
from functools import partial

if TYPE_CHECKING:
	from src.special_knock_types import SuitTuple as SuitTupleType, CardListTypeVar, Grouped_Type, OptionalSuit


BLACKS = (Suit('♣'), Suit('♠'))
REDS = (Suit('♡'), Suit('♢'))


def ListOfCardValues(grouped: Grouped_Type, suit: Suit) -> List[Rank]:
	return [card.Rank for card in grouped[suit]]


def MaxOfColour(Colour: SuitTupleType, grouped: Grouped_Type) -> Suit:
	return max((suit for suit in grouped if suit in Colour), key=partial(ListOfCardValues, grouped))


def WhicheverSuitPresent(Colour: SuitTupleType, grouped: Grouped_Type) -> Suit:
	return Colour[0 if Colour[0] in grouped else 1]


def MaxSuit(grouped: Grouped_Type) -> Suit:
	return max(grouped, key=partial(ListOfCardValues, grouped))


def SortHand(
		Hand: CardListTypeVar,
		trumpsuit: Suit,
		PlayedSuit: OptionalSuit = None,
        SuitTuple: SuitTupleType = (None, None),
        Blacks: SuitTupleType = BLACKS,
        Reds: SuitTupleType = REDS
) -> CardListTypeVar:

	if PlayedSuit:
		if PlayedSuit in SuitTuple:
			return Hand

	grouped: Grouped_Type = {}

	TrumpIsBlack = trumpsuit.IsBlack
	BlackSuitsPresent = 0

	if not PlayedSuit:
		Hand.sort(key=attrgetter('ID'), reverse=True)

	for k, g in groupby(Hand, attrgetter('Suit')):
		grouped[k] = list(g)
		if k.IsBlack:
			BlackSuitsPresent += 1

	if PlayedSuit in grouped:
		return Hand

	if (SuitNumber := len(grouped)) == 4:
		Suit1 = trumpsuit
		Suit2 = MaxOfColour((Reds if TrumpIsBlack else Blacks), grouped)

	elif SuitNumber == 3:
		if BlackSuitsPresent == 2:
			Suit1 = trumpsuit if TrumpIsBlack else MaxOfColour(Blacks, grouped)
			Suit2 = WhicheverSuitPresent(Reds, grouped)
		else:
			Suit1 = MaxOfColour(Reds, grouped) if TrumpIsBlack else trumpsuit
			Suit2 = WhicheverSuitPresent(Blacks, grouped)

	elif SuitNumber == 2:
		if PlayedSuit:
			return Hand
		if BlackSuitsPresent == 2:
			Suit1 = trumpsuit if TrumpIsBlack else MaxSuit(grouped)
			Suit2 = Suit('♡')
		elif BlackSuitsPresent:
			if trumpsuit in grouped:
				Suit1 = trumpsuit
				Suit2 = WhicheverSuitPresent((Reds if TrumpIsBlack else Blacks), grouped)
			else:
				Suit1 = MaxSuit(grouped)
				Suit2 = next(suit for suit in grouped if suit != Suit1)
		else:
			Suit1 = MaxSuit(grouped) if TrumpIsBlack else trumpsuit
			Suit2 = Suit('♣')

	else:
		return Hand

	SuitDict = {
		Suit1: 4,
		Suit2: 3,
		Suit1.OtherOfColour(): 2,
		Suit2.OtherOfColour(): 1
	}

	return sorted(Hand, key=lambda card: (SuitDict[card.Suit], card.Rank), reverse=True)
