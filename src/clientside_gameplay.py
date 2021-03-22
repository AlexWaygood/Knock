from random import randint
from traceback_with_variables import printing_exc

from src.display.display_manager import DisplayManager
from src.game.client_game import ClientGame as Game
from src.players.players_client import ClientPlayer as Player
from src.network.network_client import Client

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


class ClientsideGameplay:
	__slots__ = 'game', 'displayManager', 'typewriter', 'client', 'player', 'BiddingSystem', 'context'

	def __init__(self, playerindex: int):
		self.game = Game.OnlyGame
		self.displayManager = DisplayManager.OnlyDisplayManager
		self.typewriter = self.displayManager.Typewriter
		self.client = Client.OnlyClient
		self.player = Player.player(playerindex)
		self.BiddingSystem = self.game.BiddingSystem
		self.context = self.displayManager.InputContext

	def Play(self):
		with printing_exc():
			self.PlayTournament()

	def PlayTournament(self):
		# Menu sequence
		with self.context(TypingNeeded=True, Message='Please enter your name', font='Massive'):
			while isinstance(self.player.name, int):
				delay(100)

		self.client.BlockingMessageToServer(message='')
		delay(100)

		Args = {
			'Message': 'Waiting for all players to connect and enter their names',
			'font': 'Massive',
			'GameUpdatesNeeded': True
		}

		with self.context(**Args):
			while not Player.AllPlayersHaveJoinedTheGame():
				delay(100)

		while True:
			self.PlayGame(self.game.GamesPlayed)
			self.game.GamesPlayed += 1

	def PlayGame(self, GamesPlayed: int):
		self.GameInitialisation(GamesPlayed)
		self.AttributeWait('StartNumberSet')

		for roundnumber, cardnumber, RoundLeader in zip(*self.game.GetGameParameters()):
			self.PlayRound(roundnumber, cardnumber, RoundLeader, GamesPlayed)

		self.EndGame(GamesPlayed)

	def GameInitialisation(self, GamesPlayed: int):
		if GamesPlayed:
			Message = 'NEW GAME STARTING:'
			self.Type(Message, WaitAfterwards=1000)

		if self.playerindex() and GamesPlayed:
			text = f"Waiting for {Player.first()} to decide how many cards the game will start with."

		elif self.playerindex():
			text = f"As the first player to join this game, it is {Player.first()}'s " \
			       f"turn to decide how many cards the game will start with."

		elif GamesPlayed:
			self.Type('Your turn to decide the starting card number!')
			text = "Please enter how many cards you wish the game to start with:"

		else:
			text = "As the first player to join this game, it is your turn to decide " \
			       "how many cards you wish the game to start with:"

		self.Type(text, WaitAfterwards=0)

		with self.context(GameUpdatesNeeded=True, Message=text, font='Title'):
			self.context.TypingNeeded = not self.playerindex()
			while not self.game.StartCardNumber:
				delay(100)

		# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
		self.displayManager.GetHandRects()

		self.Type('Click to start the game for all players!', WaitAfterwards=0)

		Args = {
			'ClickToStart': True,
			'GameUpdatesNeeded': True,
			'Message': 'Click to start the game for all players!',
			'font': 'Title'
		}

		with self.context(**Args):
			while not self.game.StartPlay:
				delay(100)

		self.displayManager.GameInitialisationFade()
		self.client.QueueMessage('@A')
		self.game.StartPlay = True

	def PlayRound(
			self,
			RoundNumber: int,
			cardno: int,
			RoundLeader: Player,
			GamesPlayed: int,
	):

		self.game.StartRound(cardno, RoundLeader.playerindex, RoundNumber)

		Message = f'ROUND {RoundNumber} starting! This round has {cardno} card{"s" if cardno != 1 else ""}.'
		Message2 = f'{RoundLeader.name} starts this round.'

		for m in (Message, Message2):
			self.Type(m)

		if not GamesPlayed and RoundNumber == 1:
			Message = "Over the course of the game, your name will be underlined if it's your turn to play."
			Message2 = 'Press the Tab key at any time to toggle in and out of full-screen mode.'

			self.Type(Message)
			self.Type(Message2)

		# Wait for the server to make a new pack of cards.
		self.AttributeWait('NewPack')
		Trump = self.game.TrumpCard
		self.Type(f'The trumpcard for this round is the {Trump}, which has been removed from the pack.')

		# Wait for the server to deal cards for this round.
		self.AttributeWait('CardsDealt')

		self.displayManager.RoundStartFade()
		delay(250)

		if self.BiddingSystem == 'Classic':
			self.ClassicBidding(RoundNumber, GamesPlayed)
		else:
			self.RandomBidding(RoundNumber, cardno, GamesPlayed)

		self.client.BlockingMessageToServer()

		# Announce what all the players are bidding this round.
		for Message in Player.BidText():
			self.Type(Message)

		self.client.QueueMessage('@A')

		FirstPlayerIndex = RoundLeader.playerindex

		for i in range(cardno):
			FirstPlayerIndex = self.PlayTrick(FirstPlayerIndex, (i + 1), cardno)

		self.displayManager.RoundEndFade()

		# Award points etc.
		self.game.EndRound()
		self.client.QueueMessage('@A')

		delay(500)

		for message in Player.EndRoundText(FinalRound=(cardno == 1)):
			self.Type(message)

		self.client.QueueMessage('@A')

	def ClassicBidding(
			self,
			RoundNumber: int,
			GamesPlayed: int
	):

		if RoundNumber == 1 and not GamesPlayed:
			self.Type('Cards for this round have been dealt; each player must decide what they will bid.')

		Args = {
			'GameUpdatesNeeded': True,
			'TypingNeeded': True,
			'Message': 'Please enter your bid:',
			'font': 'Title'
		}

		with self.context(**Args):
			# We need to enter our bid.
			while self.player.Bid == -1:
				delay(100)

			# We now need to wait until everybody else has bid.
			self.context.TypingNeeded = False
			i = self.playerindex()

			while not Player.AllBid():
				delay(100)
				self.context.Text = Player.BidWaitingText(i)

	def RandomBidding(
			self,
			RoundNumber: int,
			cardnumber: int,
			GamesPlayed: int
	):

		if RoundNumber == 1 and not GamesPlayed:
			self.Type('Cards for this round have been dealt; each player must now bid.')

			self.Type(
				"The host for this game has decided that everybody's bid in this game "
				"will be randomly generated rather than decided"
			)

		Bid = randint(0, cardnumber)
		self.Type(f'Your randomly generated bid for this round is {Bid}!')

		with self.game as g:
			g.PlayerMakesBid(Bid, self.playerindex())

		self.client.QueueMessage(f'@B{Bid}')

		with self.context(GameUpdatesNeeded=True):
			while not Player.AllBid():
				delay(100)
				self.context.Text = Player.BidWaitingText(self.playerindex())

	def PlayTrick(
			self,
			FirstPlayerIndex: int,
			TrickNumber: int,
			CardNumberThisRound: int,
	):

		PlayerOrder, PosInTrick = self.game.StartTrick(TrickNumber, FirstPlayerIndex, self.player)
		self.client.QueueMessage('@A')
		Text = f'{f"TRICK {TrickNumber} starting" if CardNumberThisRound != 1 else "TRICK STARTING"}:'
		self.Type(Text)

		# Make sure the server is ready for the trick to start.
		self.AttributeWait('TrickStart')

		# Tell the server we're ready to play the trick.
		self.client.BlockingMessageToServer('@A')

		self.game.PlayTrick(self.context, PosInTrick)

		self.AttributeWait('TrickWinnerLogged')
		Winner = self.game.EndTrick()

		# Tell the server we've logged the winner
		self.client.QueueMessage('@A')

		delay(500)
		self.Type(f'{Winner} won {f"trick {TrickNumber}" if CardNumberThisRound != 1 else "the trick"}!')
		self.displayManager.TrickEndFade()

		if TrickNumber != CardNumberThisRound:
			self.client.QueueMessage('@A')

		return Winner.playerindex

	def EndGame(self, GamesPlayed: int):
		self.displayManager.DeactivateHand()

		# Announce the final scores + who won the game.
		for text in Player.GameCleanUp():
			self.Type(text)

		self.game.StartPlay = False
		delay(500)

		self.displayManager.FireworksSequence()

		# Announce who's currently won the most games in this tournament so far.
		if GamesPlayed:
			for text in Player.TournamentLeaders():
				self.Type(text)

		Message = 'Press the spacebar to play again with the same players, or close the window to exit the game.'
		self.Type(Message, WaitAfterwards=0)

		self.AttributeWait('NewGameReset', GameReset=True)
		self.game.NewGameReset()
		self.client.QueueMessage('@A')
		self.displayManager.ClearHandRects()

	def playerindex(self):
		# Has to be dynamic as the player's playerindex is liable to change
		return self.player.playerindex

	def Type(
			self,
			message: str,
			WaitAfterwards: int = 1200
	):
		self.typewriter.Type(message, WaitAfterwards=WaitAfterwards)

	def AttributeWait(
			self,
			Attribute: str,
			GameReset: bool = False
	):
		Args = {
			'GameUpdatesNeeded': True,
			'GameReset': GameReset
		}

		if GameReset:
			M = 'Press the spacebar to play again with the same players, or close the window to exit the game.'

			Args.update({
				'Message': M,
				'font': 'Title'
			})

		with self.context(**Args):
			self.game.AttributeWait(Attribute)
