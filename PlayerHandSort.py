from itertools import groupby


Blacks = ('C', 'S')
Reds = ('H', 'D')


def OtherOfColour(Suit, Blacks=Blacks):
	if Suit in Blacks:
		return 'C' if Suit == 'S' else 'S'
	return 'D' if Suit == 'H' else 'H'


def ListOfCardValues(Grouped, Suit):
	return [card.ActualValue for card in Grouped[Suit]]


def MaxOfColour(Colour, Grouped):
	return max((Suit for Suit in Grouped if Suit in Colour), key=lambda Suit: ListOfCardValues(Grouped, Suit))


def WhicheverSuitPresent(Colour, Grouped):
	return Colour[0 if Colour[0] in Grouped else 1]


def MaxSuit(Grouped):
	return max(Grouped, key=lambda Suit: ListOfCardValues(Grouped, Suit))


def SortHand(Hand, trumpsuit, PlayedSuit='', SuitTuple=('', ''), Blacks=Blacks, Reds=Reds):
	if PlayedSuit:
		if PlayedSuit in SuitTuple:
			return Hand

	Grouped = {}

	TrumpIsBlack = (trumpsuit in Blacks)
	BlackSuitsPresent = 0

	if not PlayedSuit:
		Hand.sort(key=lambda card: (card.ActualSuit, card.ActualValue), reverse=True)

	for k, g in groupby(Hand, lambda card: card.ActualSuit):
		Grouped[k] = list(g)
		if k in Blacks:
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
			Suit2 = 'H'
		elif BlackSuitsPresent:
			if trumpsuit in Grouped:
				Suit1 = trumpsuit
				Suit2 = WhicheverSuitPresent((Reds if TrumpIsBlack else Blacks), Grouped)
			else:
				Suit1 = MaxSuit(Grouped)
				Suit2 = next(suit for suit in Grouped if suit != Suit1)
		else:
			Suit1 = MaxSuit(Grouped) if TrumpIsBlack else trumpsuit
			Suit2 = 'C'

	else:
		return Hand

	SuitDict = {
		Suit1: 4,
		Suit2: 3,
		OtherOfColour(Suit1): 2,
		OtherOfColour(Suit2): 1
	}

	return sorted(Hand, key=lambda card: (SuitDict[card.ActualSuit], card.ActualValue), reverse=True)