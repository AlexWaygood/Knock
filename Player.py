from Card import Card


class Player(object):
	"""Class object for representing a single player in the game."""

	__slots__ = 'name', 'playerindex', 'Hand', 'Bid', 'Points', 'GamesWon', 'PointsThisRound', 'Tricks', 'RoundLeader', \
	            'HandIteration', 'ActionComplete', 'PointsLastRound'

	AllPlayers = []

	def __init__(self, playerindex):
		self.AllPlayers.append(self)
		self.name = playerindex
		self.playerindex = playerindex
		self.Hand = []
		self.Bid = -1
		self.Points = 0
		self.Tricks = 0
		self.PointsThisRound = 0
		self.GamesWon = 0
		self.RoundLeader = False
		self.ActionComplete = False
		self.HandIteration = 1

	def AddName(self, name):
		self.name = name
		return self

	def NextStage(self):
		self.ActionComplete = False
		return self

	@staticmethod
	def CardSortHelper(Hand, Suits):
		"""Helper method for the SortHand method below"""

		return all(any(card.ActualSuit == Suit for card in Hand) for Suit in Suits)

	@staticmethod
	def MidRoundSortHelper(Hand, SuitPlayed, SuitTuple):
		"""Helper method for the SortHand method below"""

		return all((SuitPlayed, any((any(SuitPlayed == card.ActualSuit for card in Hand), (SuitPlayed in SuitTuple)))))

	def SortHand(self, Hand, TrumpSuit, SuitPlayed='', SuitTuple=('', '')):
		"""Method to ensure the Hand is ordered black-red-black-red wherever possible"""

		if SuitPlayed and not Hand:
			return Hand

		Hand = [card.SetTrumpSuit(TrumpSuit) for card in Hand]

		if self.CardSortHelper(Hand, 'C'):
			if self.CardSortHelper(Hand, 'D'):
				if self.CardSortHelper(Hand, 'S'):
					if self.CardSortHelper(Hand, 'H'):
						if SuitPlayed:
							return Hand
						return sorted(Hand, key=Card.SuitAndValue, reverse=True)
					elif self.MidRoundSortHelper(Hand, SuitPlayed, SuitTuple):
						return Hand
					return sorted(Hand, key=Card.SuitAndValueWithoutHearts, reverse=True)
				elif self.CardSortHelper(Hand, 'H'):
					if self.MidRoundSortHelper(Hand, SuitPlayed, SuitTuple):
						return Hand
					return sorted(Hand, key=Card.SuitAndValueWithoutSpades, reverse=True)
				elif SuitPlayed:
					return Hand
			elif self.CardSortHelper(Hand, ('S', 'H')):
				if self.MidRoundSortHelper(Hand, SuitPlayed, SuitTuple):
					return Hand
				return sorted(Hand, key=Card.SuitAndValueWithoutDiamonds, reverse=True)
			elif SuitPlayed:
				return Hand
		elif self.CardSortHelper(Hand, ('D', 'S', 'H')):
			if self.MidRoundSortHelper(Hand, SuitPlayed, SuitTuple):
				return Hand
			return sorted(Hand, key=Card.SuitAndValueWithoutClubs, reverse=True)
		elif SuitPlayed:
			return Hand

		return sorted(Hand, key=Card.SuitAndValue, reverse=True)

	def ReceiveCards(self, cards, TrumpSuit):
		# Must receive an argument in the form of a list
		self.Hand = [card.AddToHand(self, i) for i, card in enumerate(self.SortHand(cards, TrumpSuit))]
		self.HandIteration += 1
		return self

	def MakeBid(self, number):
		self.Bid = int(number)
		self.ActionComplete = True
		return self

	def PlayCard(self, card, TrumpSuit):
		SuitTuple = ((Hand := self.Hand)[0].ActualSuit, Hand[-1].ActualSuit)
		Hand.remove(card)
		Suit = card.ActualSuit

		Hand = [
			card.SetPos(i) for i, card in enumerate(
				self.SortHand(Hand, TrumpSuit, SuitPlayed=Suit, SuitTuple=SuitTuple)
			)
		]

		self.Hand = Hand
		self.HandIteration += 1

	def WinsTrick(self):
		self.PointsThisRound += 1
		self.Tricks += 1
		return self

	def WinsGame(self):
		self.GamesWon += 1
		return self

	def GetPointsLastRound(self):
		"""Function for use on the client side"""

		return self.PointsLastRound

	def GetPoints(self):
		return self.Points

	def GetGamesWon(self):
		"""Function for use on the client side"""

		return self.GamesWon

	def EndOfRound(self):
		self.PointsThisRound += (10 if self.Bid == self.PointsThisRound else 0)
		self.Points += self.PointsThisRound
		self.PointsLastRound = self.PointsThisRound
		self.PointsThisRound = 0
		self.Bid = -1
		self.Tricks = 0
		self.HandIteration += 1
		return self

	def ResetPlayer(self, NewIndex):
		self.Points = 0
		self.playerindex = NewIndex
		return self

	def __repr__(self):
		return self.name if isinstance(self.name, str) else f'Player with index {self.playerindex}, as yet unnamed'
