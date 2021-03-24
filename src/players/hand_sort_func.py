from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from src.cards.server_card_suit_rank import Suit
from itertools import groupby

if TYPE_CHECKING:
	from src.special_knock_types import SuitTuple as SuitTupleType, CardListTypeVar, Grouped_Type


Blacks = (Suit('♣'), Suit('♠'))
Reds = (Suit('♡'), Suit('♢'))


def ListOfCardValues(
		grouped: Grouped_Type,
		suit: Suit
):

	return [card.Rank for card in grouped[suit]]


def MaxOfColour(
		Colour: SuitTupleType,
		grouped: Grouped_Type
):
	
	return max((suit for suit in grouped if suit in Colour), key=lambda suit: ListOfCardValues(grouped, suit))


def WhicheverSuitPresent(
		Colour: SuitTupleType,
		grouped: Grouped_Type
):
	
	return Colour[0 if Colour[0] in grouped else 1]


def MaxSuit(grouped: Grouped_Type):
	return max(grouped, key=lambda suit: ListOfCardValues(grouped, suit))


def SortHand(
		Hand: CardListTypeVar,
		trumpsuit: Suit,
		PlayedSuit: Optional[Suit] = None,
        SuitTuple: SuitTupleType = (None, None),
        Blacks=Blacks,
        Reds=Reds
) -> CardListTypeVar:

	if PlayedSuit:
		if PlayedSuit in SuitTuple:
			return Hand

	grouped: Grouped_Type = {}

	TrumpIsBlack = trumpsuit.IsBlack
	BlackSuitsPresent = 0

	if not PlayedSuit:
		Hand.sort(key=lambda card: card.ID, reverse=True)

	for k, g in groupby(Hand, lambda card: card.Suit):
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
