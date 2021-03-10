from src.Cards.Suit import Suit
from itertools import groupby


Blacks = (Suit('♣'), Suit('♠'))
Reds = (Suit('♡'), Suit('♢'))


def OtherOfColour(suit: Suit):
	if suit.IsBlack:
		return Suit('♣') if f'{suit!r}' == '♠' else Suit('♠')
	return Suit('♢') if f'{suit!r}' == '♡' else Suit('♡')


def ListOfCardValues(Grouped, suit):
	return [card.Rank for card in Grouped[suit]]


def MaxOfColour(Colour, Grouped):
	return max((suit for suit in Grouped if suit in Colour), key=lambda suit: ListOfCardValues(Grouped, suit))


def WhicheverSuitPresent(Colour, Grouped):
	return Colour[0 if Colour[0] in Grouped else 1]


def MaxSuit(Grouped):
	return max(Grouped, key=lambda suit: ListOfCardValues(Grouped, suit))


def SortHand(Hand, trumpsuit, PlayedSuit=None, SuitTuple=(None, None), Blacks=Blacks, Reds=Reds):
	"""
	@type Hand: list[src.Cards.ServerCard.ServerCard]
	@type trumpsuit: Suit
	@type PlayedSuit: Suit
	@type SuitTuple: tuple[Suit, Suit]
	@type Blacks: tuple[Suit, Suit]
	@type Reds: tuple[Suit, Suit]
	"""

	if PlayedSuit:
		if PlayedSuit in SuitTuple:
			return Hand

	Grouped = {}

	TrumpIsBlack = trumpsuit.IsBlack
	BlackSuitsPresent = 0

	if not PlayedSuit:
		Hand.sort(key=lambda card: card.ID, reverse=True)

	for k, g in groupby(Hand, lambda card: card.Suit):
		Grouped[k] = list(g)
		if k.IsBlack:
			BlackSuitsPresent += 1

	if PlayedSuit in Grouped:
		return Hand

	if (SuitNumber := len(Grouped)) == 4:
		Suit1 = trumpsuit
		Suit2 = MaxOfColour((Reds if TrumpIsBlack else Blacks), Grouped)

	elif SuitNumber == 3:
		if BlackSuitsPresent == 2:
			Suit1 = trumpsuit if TrumpIsBlack else MaxOfColour(Blacks, Grouped)
			Suit2 = WhicheverSuitPresent(Reds, Grouped)
		else:
			Suit1 = MaxOfColour(Reds, Grouped) if TrumpIsBlack else trumpsuit
			Suit2 = WhicheverSuitPresent(Blacks, Grouped)

	elif SuitNumber == 2:
		if PlayedSuit:
			return Hand
		if BlackSuitsPresent == 2:
			Suit1 = trumpsuit if TrumpIsBlack else MaxSuit(Grouped)
			Suit2 = Suit('♡')
		elif BlackSuitsPresent:
			if trumpsuit in Grouped:
				Suit1 = trumpsuit
				Suit2 = WhicheverSuitPresent((Reds if TrumpIsBlack else Blacks), Grouped)
			else:
				Suit1 = MaxSuit(Grouped)
				Suit2 = next(suit for suit in Grouped if suit != Suit1)
		else:
			Suit1 = MaxSuit(Grouped) if TrumpIsBlack else trumpsuit
			Suit2 = Suit('♣')

	else:
		return Hand

	SuitDict = {
		Suit1: 4,
		Suit2: 3,
		OtherOfColour(Suit1): 2,
		OtherOfColour(Suit2): 1
	}

	return sorted(Hand, key=lambda card: (SuitDict[card.Suit], card.Rank), reverse=True)
