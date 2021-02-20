#! Python3

"""This is the client-side script, that should be run by each player who wants to take part in the game."""

import sys, random

import pandas as pd
import matplotlib.pyplot as plt

from FireworkParticle import Particle
from FireworkSparker import Sparker
from Network import Network
from PasswordChecker import PasswordInput
from ServerUpdaters import DoubleTrigger, AttributeTracker
from PygameWrappers import SurfaceAndPosition, CoverRect, CoverRectList, RestartDisplay
from Card import Card
from GameSurface import GameSurface
from Cursors import CursorDict
from ContextHelpers import Contexts
from DataContainers import Errors, Queues, UserInput, Typewriter, Scrollwheel, FireworkVars

from HelperFunctions import GetTime, GetDimensions1, ResizeHelper, FontMachine, GetDimensions2Helper, SurfMachine, \
	CardResizer, GetHandRects

from time import time
from PIL import Image
from os import chdir, environ, path
from itertools import chain, product
from threading import Thread, Lock
from pyinputplus import inputCustom, inputMenu
from PyQt5 import QtGui
from warnings import filterwarnings
from traceback_with_variables import printing_exc

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import pygame as pg
import pygame.display as display
import pygame.key as key

from pygame.display import update as UpdateDisplay
from pygame.time import get_ticks as GetTicks
from pygame.time import delay


# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
if getattr(sys, 'frozen', False):
	chdir(sys._MEIPASS)
	filterwarnings("ignore")


class KnockTournament(object):
	"""

	Main object which contains the vast majority of the code for visualising the game on the client side.
	This object's methods also handle keyboard/mouse inputs, and various animations that happen throughout.

	"""

	__slots__ = 'Triggers', 'fonts', 'gameplayers', 'Attributes', 'player', 'Client', 'game', 'Window', 'CardImages', \
	            'Surfaces', 'PlayStarted', 'ScoreboardAttributes', 'clock', 'PlayerTextPositions', 'name', \
	            'Dimensions', 'Errors', 'ClientSideAttributes', 'PlayerNumber', 'MaxCardNumber', 'StartCardPositions', \
	            'BaseCardImages', 'CurrentColours', 'DeactivateVideoResize', 'Fullscreen', 'WindowIcon', \
	            'Scrollwheel', 'InteractiveScoreboardRequest', 'SurfacesOnScreen', 'lock', 'CoverRectOpacities',  \
	            'Contexts', 'FunctionDict', 'GameSurfMovementDict', 'cur', 'CardHoverID', 'Typewriter', \
	            'FireworkVars', 'Queues', 'UserInput', 'ColourScheme', 'BiddingSystem'

	DefaultFont = 'Times New Roman'

	FireworkSettings = {
		'FadeRate': 3,  # lower values mean fireworks fade out more slowly.
		'FPS': 600,  # Can lower this to lower the CPU usage of the fireworks display.
		'SecondsDuration': 25,

		# The lower these two numbers, the more frequent fireworks will appear.
		# The greater the gap between these two numbers, the more randomly the fireworks will be spaced.
		'Bounds': (0, 2500)
	}

	Colours = {
		'Black': (0, 0, 0),
		'Maroon': (128, 0, 0),
		'Silver': (128, 128, 128),
		'LightGrey': (204, 204, 204),
		'Black_fade': (0, 0, 0, FireworkSettings['FadeRate']),
		'Orange': (255, 136, 0)
	}

	DefaultTextColour = (0, 0, 0)
	Cursors = CursorDict

	def __init__(self, WindowDimensions, StartCardDimensions, CardImages, IP, Port, password, Theme):
		self.Fullscreen = True
		self.PlayStarted = False
		self.DeactivateVideoResize = False
		self.InteractiveScoreboardRequest = False
		self.lock = Lock()
		self.Queues = Queues()
		self.Typewriter = Typewriter()
		self.Attributes = AttributeTracker()
		self.Contexts = Contexts()
		self.UserInput = UserInput('', False)
		self.Scrollwheel = Scrollwheel(False, tuple(), 0, 0)
		self.SurfacesOnScreen = []
		self.ScoreboardAttributes = {}
		self.FireworkVars = FireworkVars(0, 0, 0)
		self.cur = ''
		self.CardHoverID = ''

		self.ColourScheme = {
			f'{x}Colour': self.Colours[y if Theme == 'Classic' else z]

			for x, y, z in zip(
				('MenuScreen', 'Silver', 'LightGrey'),
				('Scoreboard', 'Silver', 'LightGrey'),
				('GamePlayScreen', 'Maroon', 'Orange')
			)
		}

		GameSurface.AddDefaults(1186, 588)

		self.ClientSideAttributes = {
			'GamesPlayed': 0,
			'CardNumberThisRound': -1,
			'RoundNumber': 1,
			'RoundLeaderIndex': -1,
			'TrickInProgress': False,
			'TrickNumber': 0,
			'WhoseTurnPlayerIndex': -1,
			'CardPositions': [],
			'PlayerOrder': [],
			'ScrollStart': 0,
			'WindowMods': [0, 0]
		}

		self.Dimensions = {
			'ScreenSize': WindowDimensions,
			'OriginalCard': StartCardDimensions
		}

		self.Errors = Errors([], [], 0, (0, 0), None)
		self.Triggers = DoubleTrigger()

		self.CurrentColours = {
			'Game': self.Colours['LightGrey'],
			'Scoreboard': self.Colours['Maroon'],
			'Text': self.Colours['Black']
		}

		self.CoverRectOpacities = {
			'Hand': 255,
			'TrumpCard': 255,
			'Board': 255
		}

		pg.init()
		self.clock = pg.time.Clock()

		print(f'Starting attempt to connect at {GetTime()}, loading data...')

		ErrorTuple = (
			"'NoneType' object is not subscriptable",
			'[WinError 10061] No connection could be made because the target machine actively refused it'
		)

		# Connect to the server
		# Remember - this part of the code will fail if the server's network router does not have port forwarding set up.
		# (Warning does not apply if you are playing within one local area network.)

		Time = time()

		while True:
			try:
				self.Client = Network(IP, Port, password=password)
				self.game = self.Client.InfoDict['game']
				self.player = self.Client.InfoDict['player']
				self.BiddingSystem = self.Client.InfoDict['BiddingSystem']
				break
			except (TypeError, ConnectionRefusedError) as e:
				if str(e) in ErrorTuple:
					print('Initial connection failed; has the server been initialised?')
					print('Further attempts will be made to connect until a connection is successful.')
					continue
				raise e
			except OSError as e:
				if str(e) == '[WinError 10051] A socket operation was attempted to an unreachable network':
					print("OSError. Check you're connected to the internet?")
					raise e

			if (CurrentTime := time()) > Time + 5:
				print(
					"Connection failed; trying again. "
					"Check that the server script is running and you're connected to the internet."
				)

				Time = CurrentTime

		print(f'Connected at {GetTime()}.')

		assert self.game, "Couldn't get a copy of the game. Have the maximum number of players already joined?"

		self.name = self.player.playerindex
		self.PlayerNumber = self.game.PlayerNumber
		self.MaxCardNumber = 51 // self.PlayerNumber
		self.gameplayers = self.game.gameplayers
		self.StartCardPositions = list(range(self.PlayerNumber))
		self.WindowIcon = pg.image.load(path.join('CardImages', 'PygameIcon.png'))
		self.InitialiseWindow(WindowDimensions, pg.RESIZABLE)

		self.Surfaces = {
			'BaseScoreboard': tuple(),
			'Game': GameSurface(*WindowDimensions, self.Colours['LightGrey'])
		}

		RestartDisplay()
		self.RedrawWindow(WindowDimensions=WindowDimensions)
		key.set_repeat(1000, 50)

		self.BaseCardImages = {
			ID: pg.image.fromstring(image.tobytes(), image.size, image.mode).convert()
			for ID, image in CardImages.items()
		}

		self.GetDimensions2(FromInit=True)
		self.UpdateGameAttributes()

		GameSurf = self.Surfaces['Game']

		self.GameSurfMovementDict = {
			'arrow': lambda x: GameSurf.ArrowKeyMove(x),
			'mouse': lambda x: GameSurf.MouseMove(x),
			'centre': lambda x: GameSurf.MoveToCentre(),
			'scrollwheel': lambda x: GameSurf.ScrollwheelDownMove(x)
		}

		print(f'Game display now initialising at {GetTime()}...')
		Thread(target=self.ThreadedGameUpdate, daemon=True).start()
		self.Errors.StartTime = GetTicks()
		Thread(target=self.PlayTournament, daemon=True).start()

		while True:
			self.GameLoop()

	def PlayTournament(self):
		# Menu sequence

		with self.Contexts.Input(TypingNeeded=True, Message='Please enter your name', font='Massive'):
			while isinstance(self.name, int):
				delay(100)

		while not self.Queues.ServerComms.empty():
			delay(100)

		delay(100)

		Args = {
			'Message': 'Waiting for all players to connect and enter their names',
			'font': 'Massive',
			'GameUpdatesNeeded': True
		}

		with self.Contexts.Input(**Args):
			while not self.gameplayers.AllPlayersHaveJoinedTheGame():
				delay(100)
				self.gameplayers = self.game.gameplayers

		while True:
			self.PlayGame(self.ClientSideAttributes['GamesPlayed'])
			self.ClientSideAttributes['GamesPlayed'] += 1

	def PlayGame(self, GamesPlayed):
		self.GameInitialisation(GamesPlayed)
		self.AttributeWait('StartNumberSet')

		for roundnumber, cardnumber, RoundLeader in zip(*self.game.GetGameParameters()):
			self.StartRound(roundnumber, cardnumber, RoundLeader, GamesPlayed)
			FirstPlayerIndex = RoundLeader.playerindex

			for i in range(cardnumber):
				FirstPlayerIndex = self.PlayTrick(FirstPlayerIndex, (i + 1), cardnumber)

			self.EndRound(FinalRound=(cardnumber == 1))

		self.EndGame(GamesPlayed)

	def GameInitialisation(self, GamesPlayed):
		self.CurrentColours['Game'] = 'Maroon' if GamesPlayed else 'LightGrey'

		if GamesPlayed:
			Message = 'NEW GAME STARTING:'
			self.Typewriter.Type(Message, WaitAfterwards=1000)

		if self.player.playerindex and GamesPlayed:
			text = f"Waiting for {self.gameplayers[0]} to decide how many cards the game will start with."

		elif self.player.playerindex:
			text = f"As the first player to join this game, it is {self.gameplayers[0]}'s " \
			       f"turn to decide how many cards the game will start with."

		elif GamesPlayed:
			Message2 = 'Your turn to decide the starting card number!'
			self.Typewriter.Type(Message2)
			text = "Please enter how many cards you wish the game to start with:"

		else:
			text = "As the first player to join this game, it is your turn to decide " \
			       "how many cards you wish the game to start with:"

		self.Typewriter.Type(text, WaitAfterwards=0)

		with self.Contexts.Input(GameUpdatesNeeded=True, Message=text, font='Title'):
			self.Contexts.Input.TypingNeeded = not self.player.playerindex
			while not self.Attributes.StartCardNumber:
				delay(100)

		# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
		self.CalculateHandRects(
			self.Surfaces['Game'].RectWidth,
			self.Dimensions['WindowMargin'],
			self.Dimensions['Card'][0]
		)

		self.Typewriter.Type('Click to start the game for all players!', WaitAfterwards=0)

		Args = {
			'ClickToStart': True,
			'GameUpdatesNeeded': True,
			'Message': 'Click to start the game for all players!',
			'font': 'Title'
		}

		with self.Contexts.Input(**Args):
			while not self.game.StartPlay:
				delay(100)

		if not GamesPlayed:
			with self.Contexts.Fades(BoardColour=True):
				self.Fade(colour1='LightGrey', colour2='Maroon')

		self.Queues.SurfaceUpdates.put(['ScoreboardFromScratch'])
		self.SurfacesOnScreen.append('Scoreboard')

		with self.Contexts.Fades(Scoreboard=True):
			self.Fade(colour1='Maroon', colour2='LightGrey', ScoreboardFade=True)

		self.Queues.ServerComms.put('AC')
		self.PlayStarted = True

	def StartRound(self, RoundNumber, cardnumber, RoundLeader, GamesPlayed):
		self.ClientSideAttributes.update({
			'CardNumberThisRound': cardnumber,
			'RoundLeaderIndex': RoundLeader.playerindex,
			'RoundNumber': RoundNumber
		})

		Message = f'ROUND {RoundNumber} starting! This round has {cardnumber} card{"s" if cardnumber != 1 else ""}.'
		Message2 = f'{RoundLeader.name} starts this round.'

		for m in (Message, Message2):
			self.Typewriter.Type(m)

		if not GamesPlayed and RoundNumber == 1:
			Message = "Over the course of the game, your name will be underlined if it's your turn to play."
			Message2 = 'Press the Tab key at any time to toggle in and out of full-screen mode.'

			self.Typewriter.Type(Message)
			self.Typewriter.Type(Message2)

		# Wait for the server to make a new pack of cards.
		self.AttributeWait('NewPack')
		Trump = self.Attributes.TrumpCard.VerboseString
		self.Typewriter.Type(f'The trumpcard for this round is the {Trump}, which has been removed from the pack.')

		# Wait for the server to deal cards for this round.
		self.AttributeWait('CardsDealt')

		# Fade in the *player text on the board only*, then the cards in your hand + the trumpcard.
		self.CurrentColours['Text'] = self.Colours['Maroon']

		for string in ('TrumpCard', 'Hand'):
			self.Surfaces[string].SetCoverRectOpacity(255)

		with self.Contexts.Fades(TrumpCard=True, Hand=True):
			self.SurfacesOnScreen += ['Board', 'TrumpCard']
			self.Fade(colour1='Maroon', colour2=(0, 0, 0), FadeIn=True, TextFade=True)
			self.SurfacesOnScreen.append('Hand')
			self.Fade(CardFade=True, FadeIn=True)

		delay(250)

		if self.BiddingSystem == 'Classic':
			self.ClassicBidding(RoundNumber, GamesPlayed)
		else:
			self.RandomBidding(RoundNumber, cardnumber, GamesPlayed)

		# (Refresh the board.)
		self.UpdateAttributesWithLock()

		# Announce what all the players are bidding this round.
		for Message in self.gameplayers.BidText():
			self.Typewriter.Type(Message)

		self.Queues.ServerComms.put('AC')

	def ClassicBidding(self, RoundNumber, GamesPlayed):
		if RoundNumber == 1 and not GamesPlayed:
			self.Typewriter.Type('Cards for this round have been dealt; each player must decide what they will bid.')

		# We need to enter our bid.

		Args = {
			'GameUpdatesNeeded': True,
			'TypingNeeded': True,
			'Message': 'Please enter your bid:',
			'font': 'Title'
		}

		with self.Contexts.Input(**Args):
			while self.player.Bid == -1:
				delay(100)

			# We now need to wait until everybody else has bid.
			self.Contexts.Input.TypingNeeded = False
			i = self.player.playerindex

			while not self.gameplayers.AllBid():
				delay(100)
				self.Contexts.Input.Message = self.gameplayers.BidWaitingText(i)

			self.BlockingMessageToServer()

	def RandomBidding(self, RoundNumber, cardnumber, GamesPlayed):
		if RoundNumber == 1 and not GamesPlayed:
			self.Typewriter.Type('Cards for this round have been dealt; each player must now bid.')

			self.Typewriter.Type(
				"The host for this game has decided that everybody's bid in this game "
				"will be randomly generated rather than decided"
			)

		Bid = random.randint(0, cardnumber)
		self.Typewriter.Type(f'Your randomly generated bid for this round is {Bid}!')

		with self.lock:
			self.game.PlayerMakesBid(Bid, player=self.player)

		self.Queues.ServerComms.put(('Bid', Bid))

		with self.Contexts.Input(GameUpdatesNeeded=True):
			while not self.gameplayers.AllBid():
				delay(100)
				self.Contexts.Input.Message = self.gameplayers.BidWaitingText(self.player.playerindex)
			self.BlockingMessageToServer()

	def PlayTrick(self, FirstPlayerIndex, TrickNumber, CardNumberThisRound):
		self.ClientSideAttributes.update({
			'TrickInProgress': True,
			'TrickNumber': TrickNumber,
		})

		List1, List2 = self.StartCardPositions[FirstPlayerIndex:],  self.StartCardPositions[:FirstPlayerIndex]
		self.ClientSideAttributes['CardPositions'] = List1 + List2

		PlayerNo = self.PlayerNumber

		PlayerOrder = list(chain(range(FirstPlayerIndex, PlayerNo), range(FirstPlayerIndex)))
		self.ClientSideAttributes['PlayerOrder'] = PlayerOrder

		self.player.PosInTrick = Pos = PlayerOrder.index(self.player.playerindex)
		self.Queues.ServerComms.put('AC')
		self.Queues.SurfaceUpdates.put(['Board', 'TrumpCard', 'Hand', 'Scoreboard'])
		Text = f'{f"TRICK {TrickNumber} starting" if CardNumberThisRound != 1 else "TRICK STARTING"}:'
		self.Typewriter.Type(Text)

		# Make sure the server is ready for the trick to start.
		self.AttributeWait('TrickStart')

		# Tell the server we're ready to play the trick.
		self.BlockingMessageToServer('AC', UpdateGameAttributes=True)

		with self.Contexts.Input(GameUpdatesNeeded=True):
			# Play the trick, wait for all players to play.
			for i in range(PlayerNo):
				self.ClientSideAttributes['WhoseTurnPlayerIndex'] = PlayerOrder[i]

				while (CardsOnBoard := len(self.Attributes.PlayedCards)) == i:
					delay(100)
					self.Queues.SurfaceUpdates.put(['Board', 'Hand'])
					self.Contexts.Input.TrickClickNeeded = (CardsOnBoard == Pos)

		self.AttributeWait('TrickWinnerLogged')
		PlayedCards, trumpsuit = self.Attributes.PlayedCards, self.Attributes.trumpsuit
		WinningCard = max(PlayedCards, key=lambda card: card.GetWinValue(PlayedCards[0].Suit, trumpsuit))
		(Winner := self.gameplayers[WinningCard.PlayedBy]).WinsTrick()

		# Tell the server we've logged the winner
		self.Queues.ServerComms.put('AC')

		if TrickNumber != CardNumberThisRound:

			self.ClientSideAttributes.update({
				'WhoseTurnPlayerIndex': -1,
				'TrickInProgress': False
			})

			self.UpdateGameAttributes()

		delay(500)
		Text = f'{Winner} won {f"trick {TrickNumber}" if CardNumberThisRound != 1 else "the trick"}!'
		self.Typewriter.Type(Text)

		# Fade out the cards on the board
		with self.Contexts.Fades(BoardCards=True):
			self.Fade(FadeIn=False, CardFade=True, TimeToTake=300, EndOfTrickFade=True)
			self.Attributes.PlayedCards.clear()

		self.Queues.SurfaceUpdates.put(['Board'])

		if TrickNumber != CardNumberThisRound:
			self.Queues.ServerComms.put('AC')

		return Winner.playerindex

	def EndRound(self, FinalRound: bool):
		self.BuildScoreboard('LightGrey')
		self.BlitSurface('Game', 'Scoreboard')

		# Fade out the trumpcard, then the text on the board
		self.Surfaces['TrumpCard'].SetCoverRectOpacity(0)

		with self.Contexts.Fades(TrumpCard=True):
			self.Fade(FadeIn=False, CardFade=True)
			self.Attributes.TrumpCard = None
			self.Fade(colour1=(0, 0, 0), colour2='Maroon', FadeIn=False, TextFade=True)

			for string in ('Board', 'TrumpCard'):
				self.SurfacesOnScreen.remove(string)

		self.ClientSideAttributes.update({'WhoseTurnPlayerIndex': -1, 'TrickInProgress': False})
		self.UpdateGameAttributes()

		# Award points.
		self.game.RoundCleanUp(self.gameplayers)

		if self.ClientSideAttributes['RoundNumber'] != self.Attributes.StartCardNumber:
			self.ClientSideAttributes['RoundNumber'] += 1
			self.ClientSideAttributes['CardNumberThisRound'] -= 1
			self.ClientSideAttributes['TrickNumber'] = 1

		self.UpdateGameAttributes()
		self.BuildScoreboard()
		self.Queues.ServerComms.put('AC')

		delay(500)

		for message in self.gameplayers.EndRoundText(FinalRound=FinalRound):
			self.Typewriter.Type(message)

		self.Queues.ServerComms.put('AC')

	def EndGame(self, GamesPlayed):
		self.SurfacesOnScreen.remove('Hand')

		# Announce the final scores + who won the game.
		for text in self.gameplayers.GameCleanUp():
			self.Typewriter.Type(text)

		self.PlayStarted = False
		delay(500)

		# Fade the screen out incrementally to prepare for the fireworks display
		with self.Contexts.Fades(Scoreboard=True):
			self.Fade(colour1='LightGrey', colour2='Maroon', ScoreboardFade=True)

		with self.Contexts.Fades(BoardColour=True):
			self.Fade(colour1='Maroon', colour2=(0, 0, 0), FadeIn=False)
		self.SurfacesOnScreen.clear()

		# This part of the code adapted from code by Adam Binks
		self.FireworkVars.LastFirework = GetTicks()
		self.FireworkVars.EndTime = self.FireworkVars.LastFirework + (self.FireworkSettings['SecondsDuration'] * 1000)
		self.FireworkVars.RandomAmount = random.randint(*self.FireworkSettings['Bounds'])

		with self.Contexts.Input(FireworksInProgress=True):
			while GetTicks() < self.FireworkVars.EndTime or Particle.allParticles:
				delay(100)

		# Fade the screen back to maroon after the fireworks display.
		with self.Contexts.Fades(BoardColour=True):
			self.Fade(colour1=(0, 0, 0), colour2='Maroon')

		delay(1000)

		# Announce who's currently won the most games in this tournament so far.
		if GamesPlayed:
			for text in self.gameplayers.TournamentLeaders():
				self.Typewriter.Type(text)

		Message = 'Press the spacebar to play again with the same players, or close the window to exit the game.'
		self.Typewriter.Type(Message, WaitAfterwards=0)

		self.AttributeWait('NewGameReset', GameReset=True)
		self.game.NewGameReset()
		self.gameplayers.NewGame()
		self.player.ResetPlayer(self.PlayerNumber)
		self.Surfaces['BaseScoreboard'] = None
		self.Queues.ServerComms.put('AC')
		self.Surfaces['Hand'].ClearRectList()
		self.ClientSideAttributes['RoundNumber'] = 1

	def ThreadedGameUpdate(self):
		"""This method runs throughout gameplay on a separate thread."""

		while True:
			delay(100)

			if self.Queues.ServerComms.empty():
				if self.Contexts.Input.GameUpdatesNeeded:
					self.GetGame()
			else:
				if isinstance((message := self.Queues.ServerComms.get()), str):
					self.GetGame(message)
				else:
					self.SendToServer(*message)

	def BlockingMessageToServer(self, message='', UpdateGameAttributes=False):
		Q = self.Queues.ServerComms

		if message:
			Q.put(message)

		while not Q.empty():
			delay(100)

		if UpdateGameAttributes:
			self.UpdateGameAttributes()

	def Fill(self, SurfaceObject, colour=None, CurrentColour=False):
		if CurrentColour:
			return self.Fill(
				SurfaceObject,
				self.CurrentColours['Scoreboard' if SurfaceObject == 'Scoreboard' else 'Game']
			)

		if isinstance(SurfaceObject, str):
			SurfaceObject = self.Surfaces[SurfaceObject]

		if colour and isinstance(colour, str):
			colour = self.ColourScheme[colour]

		SurfaceObject.fill(colour)
		return SurfaceObject

	def GetPlayer(self):
		return self.game.gameplayers[self.name]

	def UpdateGameAttributes(self):
		"""

		Upon receiving an updated copy of the game from the server...
		...This method ensures an immediate update of the client-side copies of all the game's attributes

		"""

		Trump = self.game.Attributes.TrumpCard
		CardLists = (self.GetPlayer().Hand, self.game.Attributes.PlayedCards, ((Trump,) if Trump else tuple()))
		PlayerOrder, Surfaces = self.ClientSideAttributes['PlayerOrder'], self.Surfaces

		for CardList, ListName in zip(CardLists, ('Hand', 'Board', 'TrumpCard')):
			CardList = [
				card.UpdateOnArrival(i, ListName, PlayerOrder, Surfaces, self.CardImages)
				for i, card in enumerate(CardList)
			]

		self.player.ServerUpdate(self.GetPlayer())
		self.gameplayers.UpdateFromServer(self.game.gameplayers)
		self.Attributes = self.game.Attributes
		self.Triggers.Server = self.game.Triggers

	def ReceiveGame(self, GameFromServer):
		if GameFromServer != self.game:
			self.game = GameFromServer
			if self.Queues.ServerComms.empty():
				self.UpdateAttributesWithLock()

	def GetGame(self, arg='GetGame'):
		self.ReceiveGame(self.Client.ClientSimpleSend(arg))

	def SendToServer(self, MessageType, Message):
		self.ReceiveGame(self.Client.send(MessageType, Message))

	def RedrawWindow(self, WindowDimensions=None, FromFullScreen=False, ToFullScreen=False):
		x, y = self.Dimensions['ScreenSize']

		if FromFullScreen:
			x, y = (x - 100), (y - 100)
			RestartDisplay()
		elif not ToFullScreen:
			x, y = WindowDimensions

		self.InitialiseWindow((x, y), (pg.FULLSCREEN if ToFullScreen else pg.RESIZABLE))
		self.Window.fill(self.CurrentColours['Game'])
		GameSurf, GameSurfColour = self.Surfaces['Game'], self.CurrentColours['Game']

		if ToFullScreen or FromFullScreen or (x, y) != (GameSurf.RectWidth, GameSurf.RectHeight):
			self.Surfaces['Game'] = GameSurf.NewWindowSize((x, y), GameSurfColour, (ToFullScreen or FromFullScreen))
			self.GetDimensions2()
			self.Dimensions['Window'] = (x, y)

	def GetDimensions2(self, FromInit=False):
		NewGameDimensions, CurrentCardDimensions = self.Surfaces['Game'].Dimensions, self.Dimensions['OriginalCard']
		WindowMargin, NewCardDims, ResizeRatio = GetDimensions1(NewGameDimensions, CurrentCardDimensions)
		GameX, GameY, CardX, CardY = *NewGameDimensions, *NewCardDims

		Dimensions = {
			'WindowMargin': WindowMargin,
			'Card': NewCardDims
		}

		CardImages = CardResizer(ResizeRatio, self.BaseCardImages)
		fonts = FontMachine(self.DefaultFont, GameX, GameY)
		SurfaceAndPosition.AddDefaults(NewCardDims, self.ColourScheme['GamePlayScreenColour'])
		CommonArgs = (GameX, GameY, CardX, CardY, WindowMargin)

		(

			TrumpCardPos, TrumpCardSurfaceDimensions, CardRectsOnBoard,
			ErrorPos, BoardCentre, PlayerTextPositions, BoardPos

		) = GetDimensions2Helper(*CommonArgs, fonts['Normal'].linesize, self.PlayerNumber)

		Surfs = SurfMachine(
			self.CurrentColours['Scoreboard'],
			TrumpCardSurfaceDimensions,
			*CommonArgs,
			TrumpCardPos,
			self.CoverRectOpacities,
			BoardPos,
			self.Dimensions['ScreenSize'],
			CardRectsOnBoard,
			self.Colours['Black_fade']
		)

		# If we're calling it from Init, the Surfaces dict won't be formed yet,
		# so calling bool() as below will result in Key Error.
		HandRectsNeeded = False if FromInit else bool(self.Surfaces['Hand'].RectList)

		self.CardImages = CardImages
		self.Errors.Pos = ErrorPos
		self.Dimensions['BoardCentre'] = BoardCentre
		self.fonts = fonts
		self.Surfaces.update(Surfs)

		if self.Surfaces['BaseScoreboard']:
			self.ScoreboardAttributes = {}
			self.BuildBaseScoreboard()
			self.BuildScoreboard(self.CurrentColours['Scoreboard'])

		self.PlayerTextPositions = PlayerTextPositions
		self.Dimensions.update(Dimensions)

		if HandRectsNeeded:
			self.CalculateHandRects(GameX, WindowMargin, CardX)
			self.UpdateGameAttributes()

		self.UpdateSurfaces(ToUpdate=['Scoreboard', 'Hand', 'TrumpCard', 'Board'])

		Args = (
			(self.Contexts.Fades.BoardCards, self.Contexts.Fades.TrumpCard, self.Contexts.Fades.Hand),
			('Board', 'TrumpCard', 'Hand')
		)

		for arg1, arg2 in zip(*Args):
			if arg1:
				self.BlitSurface(arg2, self.Surfaces[arg2].CoverRects)

	def CalculateHandRects(self, GameSurfX, WindowMargin, CardX):
		self.Surfaces['Hand'].AddRectList(
			GetHandRects(GameSurfX, WindowMargin, CardX, self.Attributes.StartCardNumber),
			self.CoverRectOpacities['Hand'],
			self.CurrentColours['Game']
		)

	def UpdateWindow(self, List=None):
		if List:
			self.Fill('Game', CurrentColour=True)
			self.BlitSurface('Game', List)
		self.BlitSurface(self.Window, 'Game')
		UpdateDisplay()

	def QuitGame(self):
		pg.quit()
		self.Client.CloseDown()
		raise Exception('Game has ended.')

	def GameSurfMove(self, Type, arg):
		if Type == 'scrollwheel':
			self.Scrollwheel.DownTime = GetTicks()
			
		with self.lock:
			self.GameSurfMovementDict[Type](arg)
			self.UpdateGameAttributes()

	def GameLoop(self):
		""" Main game loop """

		Condition = (len(self.gameplayers) != self.PlayerNumber and self.game.StartPlay)

		if Condition or not display.get_init() or not display.get_surface():
			self.QuitGame()

		if self.Contexts.Input.FireworksDisplay:
			self.FireworkDisplay()
		else:
			self.StandardScreenBuild()

		UpdateDisplay()
		self.Errors.ThisPass.clear()
		self.UserInput.click = False

		for event in pg.event.get():
			self.HandleEvent(event)

		if self.Scrollwheel.IsDown and GetTicks() > (self.Scrollwheel.DownTime + 20):
			self.GameSurfMove('scrollwheel', self.Scrollwheel.DownPos)

		if not self.Contexts.Input.InputNeeded():
			return None

		if self.UserInput.click:
			self.HandleClicks()

		if self.Errors.ThisPass:
			self.ErrorMessages()

		if self.Errors.Messages and GetTicks() > self.Errors.StartTime + 5000:
			self.Errors.Messages.clear()

		while len(self.Errors.Messages) > 5:
			self.Errors.Messages.pop()

	def AttributeWait(self, Attribute, GameReset=False):
		"""
		Three methods follow below that work together...
		...to allow the client-side script to 'do nothing' for a set period of time.
		"""

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

		with self.Contexts.Input(**Args):
			while self.Triggers.Server.Events[Attribute] == self.Triggers.Client.Events[Attribute]:
				delay(100)

			self.Triggers.Client.Events[Attribute] = self.Triggers.Server.Events[Attribute]

	def BlitSurface(self, arg1, arg2, CardFade=False):
		"""
		Method for simplifying the blitting of one surface -- or a list of surfaces -- to another.
		Arg1 refers, directly or indirectly, to a base surface.
		Arg2 refers, directly or indirectly, to a second surface to be blitted onto that base surface.
		"""

		# If arg1 is a string, we look it up in the self.Surfaces dictionary
		if isinstance(arg1, str):
			arg1 = self.Surfaces[arg1]

		if isinstance(arg2, list) or isinstance(arg2, chain):
			# We can't use .blits in this situation
			# We don't know if arg2 is a list of cards or a list of surface objects

			for item in arg2:
				self.BlitSurface(arg1, item)

		elif isinstance(arg2, CoverRectList):
			arg1.blits([cv.surfandrect for cv in arg2])

		elif isinstance(arg2, tuple):
			if callable(arg2[1]):
				self.BlitSurface(arg1, (arg2[0], arg2[1]()))
			elif isinstance(arg2[0], pg.Surface):
				arg1.blit(*arg2)

		elif isinstance(arg2, CoverRect):
			arg1.blit(*arg2.surfandrect)

		# If arg2 is a SurfaceAndPosition object, we use its .surfandpos attribute
		elif isinstance(arg2, SurfaceAndPosition) or isinstance(arg2, Card):
			arg1.blit(*arg2.surfandpos)

		elif arg2 is None:
			pass

		# If arg2 is a string, we look it up in the self.Surfaces dictionary
		elif isinstance(arg2, str):
			try:
				arg1.blit(*self.Surfaces[arg2].surfandpos)
			except AttributeError as e:
				if arg2 == 'Scoreboard':
					self.BuildScoreboard(self.CurrentColours['Scoreboard'])
					arg1.blit(*self.Surfaces[arg2].surfandpos)
				else:
					raise e

		if CardFade and isinstance(arg1, SurfaceAndPosition):
			arg1.SetCoverRectOpacity(self.CoverRectOpacities[f'{arg1}'])
			self.BlitSurface(arg1, arg1.CoverRects)

		return arg1

	def GetText(self, text, font='Normal', colour=(0, 0, 0), pos=None, leftAlign=False, rightAlign=False):
		"""Function to generate rendered text and a pygame Rect object"""

		if pos:
			pos = (int(pos[0]), int(pos[1]))
		else:
			pos = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Surfaces['Game'].centre

		text = (self.fonts[font]).render(text, False, colour)

		if leftAlign:
			rect = text.get_rect(topleft=pos)
		else:
			rect = text.get_rect(topright=pos) if rightAlign else text.get_rect(center=pos)

		return text, rect

	def SetScoreboardAttribute(self, Attribute, Value):
		"""Helper function for the Scoreboard-building functions below"""

		self.ScoreboardAttributes[Attribute] = self.ScoreboardAttributes.get(Attribute, Value)
		return self.ScoreboardAttributes[Attribute]

	def BuildBaseScoreboard(self):
		NormalLineSize = self.fonts['Normal'].linesize
		LeftMargin = self.SetScoreboardAttribute('LeftMargin', int(NormalLineSize * 1.75))
		TitlePos = self.SetScoreboardAttribute('TitlePos', int(NormalLineSize * 1.5))
		MaxPointsText = max(self.fonts['Normal'].size(f'{str(player)}: 88 points')[0] for player in self.gameplayers)

		ScoreboardWidth = self.SetScoreboardAttribute(
			'Width',
			(2 * LeftMargin) + max(MaxPointsText, self.fonts['UnderLine'].size('Trick not in progress')[0])
		)

		GamesPlayed = self.ClientSideAttributes['GamesPlayed']
		Multiplier = ((self.PlayerNumber * 2) + 7) if GamesPlayed else (self.PlayerNumber + 4)
		ScoreboardHeight = (NormalLineSize * Multiplier) + (2 * LeftMargin)
		self.Surfaces['BaseScoreboard'] = (ScoreboardWidth, ScoreboardHeight)
		self.SetScoreboardAttribute('Centre', (ScoreboardWidth // 2))

		self.SetScoreboardAttribute(
			'Title',
			self.GetText('SCOREBOARD', font='UnderLine', pos=(self.ScoreboardAttributes['Centre'], TitlePos))
		)

	def ScoreboardHelper(self, LeftMargin, y, ScoreboardBlits, Gen):
		for Message in Gen:
			Pos2 = ((self.ScoreboardAttributes['Width'] - LeftMargin), y)
			args = zip(range(2), ((LeftMargin, y), Pos2), (True, False), (False, True))
			ScoreboardBlits += [self.GetText(Message[a], pos=b, leftAlign=c, rightAlign=d) for a, b, c, d in args]
			y += self.fonts['Normal'].linesize

		return ScoreboardBlits, y

	def BuildScoreboard(self, ScoreboardColour=None):
		if not self.Surfaces['BaseScoreboard']:
			self.BuildBaseScoreboard()

		if not ScoreboardColour:
			ScoreboardColour = self.Colours['LightGrey']
		elif isinstance(ScoreboardColour, str):
			ScoreboardColour = self.Colours[ScoreboardColour]

		SurfDimensions = self.Surfaces['BaseScoreboard']
		ScoreboardBlits = [self.ScoreboardAttributes['Title']]
		NormalLineSize = self.fonts['Normal'].linesize
		y = self.ScoreboardAttributes['TitlePos'] + NormalLineSize
		LeftMargin = self.ScoreboardAttributes['LeftMargin']
		ScoreboardBlits, y = self.ScoreboardHelper(LeftMargin, y, ScoreboardBlits, self.gameplayers.ScoreboardText())
		y += NormalLineSize * 2
		TrickNo, CardNo = self.ClientSideAttributes["TrickNumber"], self.ClientSideAttributes["CardNumberThisRound"]
		RoundNo, StartCardNo = self.ClientSideAttributes['RoundNumber'], self.Attributes.StartCardNumber
		Message1 = self.GetText(f'Round {RoundNo} of {StartCardNo}', pos=(self.ScoreboardAttributes['Centre'], y))
		TrickText = f'Trick {TrickNo} of {CardNo}' if TrickNo else 'Trick not in progress'
		Message2 = self.GetText(TrickText, pos=(self.ScoreboardAttributes['Centre'], (y + NormalLineSize)))
		ScoreboardBlits += [Message1, Message2]

		if self.ClientSideAttributes['GamesPlayed']:
			y += NormalLineSize * 3
			ScoreboardBlits.append(self.GetText('-----', pos=(self.ScoreboardAttributes['Centre'], y)))
			y += NormalLineSize
			Gen = self.gameplayers.ScoreboardText2()
			ScoreboardBlits, y = self.ScoreboardHelper(LeftMargin, y, ScoreboardBlits, Gen)

		self.Surfaces['Scoreboard'].AddSurf(SurfaceDimensions=SurfDimensions, FillColour=ScoreboardColour)
		self.BlitSurface('Scoreboard', ScoreboardBlits)

	def BuildPlayerHand(self, CardFade=False):
		self.Fill('Hand', 'GamePlayScreenColour')
		self.BlitSurface('Hand', self.player.Hand)

		if CardFade:
			self.BlitSurface('Hand', self.Surfaces['Hand'].CoverRects)

		self.Triggers.Client.Surfaces['Hand'] = self.player.HandIteration

	def BuildBoardSurface(self, CardFade=False):
		self.Fill('Board', 'GamePlayScreenColour')

		BoardSurfaceBlits = self.Attributes.PlayedCards.copy()
		TextColour = self.CurrentColours['Text']

		Args = (
			self.ClientSideAttributes['WhoseTurnPlayerIndex'],
			self.ClientSideAttributes['TrickInProgress'],
			len(self.Attributes.PlayedCards),
			self.gameplayers.AllBid(),
			self.gameplayers.PlayerNo,
			self.fonts['Normal'].linesize,
			self.ClientSideAttributes['RoundLeaderIndex']
		)

		Positions = self.PlayerTextPositions
		T = sum([player.BoardText(*Args, *Positions[i]) for i, player in enumerate(self.gameplayers)], start=[])
		BoardSurfaceBlits += [self.GetText(Tuple[0], font=Tuple[1], colour=TextColour, pos=Tuple[2]) for Tuple in T]
		self.BlitSurface('Board', BoardSurfaceBlits, CardFade=CardFade)
		self.Triggers.Client.Surfaces['Board'] = self.Triggers.Server.Surfaces['Board']

	def BuildTrumpCardSurface(self, CardFade=False):
		Trump = self.Attributes.TrumpCard
		self.Fill('TrumpCard', 'GamePlayScreenColour')
		Pos = (self.Surfaces['TrumpCard'].midpoint, (self.fonts['Normal'].linesize // 2))
		Text = self.GetText('Trumpcard', colour=self.CurrentColours['Text'], pos=Pos)
		self.BlitSurface('TrumpCard', [Text, Trump], CardFade=CardFade)
		self.Triggers.Client.Surfaces['TrumpCard'] = self.Triggers.Server.Surfaces['TrumpCard']

	def SurfaceUpdateRequired(self, name):
		return (
				self.Triggers.Server.Surfaces[name] != self.Triggers.Client.Surfaces[name]
				and name in self.SurfacesOnScreen
		)

	def UpdateSurfaces(self, ToUpdate=None):
		if ('ScoreboardFromScratch' in ToUpdate
				or (self.Surfaces['BaseScoreboard']
				    and (self.SurfaceUpdateRequired('Scoreboard') or 'Scoreboard' in ToUpdate)
				)
		):
			try:
				self.BuildScoreboard(self.CurrentColours['Scoreboard'])
			except:
				pass

		Condition = (self.player.HandIteration > self.Triggers.Client.Surfaces['Hand']) or ('Hand' in ToUpdate)

		if (self.Contexts.Fades.BoardColour or Condition) and 'Hand' in self.SurfacesOnScreen:
			try:
				self.BuildPlayerHand(CardFade=self.Contexts.Fades.Hand)
			except:
				pass

		if self.SurfaceUpdateRequired('Board') or self.Contexts.Fades.BoardColour or 'Board' in ToUpdate:
			try:
				self.BuildBoardSurface(CardFade=self.Contexts.Fades.BoardCards)
			except:
				pass

		if self.SurfaceUpdateRequired('TrumpCard') or self.Contexts.Fades.BoardColour or 'TrumpCard' in ToUpdate:
			try:
				self.BuildTrumpCardSurface(CardFade=self.Contexts.Fades.TrumpCard)
			except:
				pass

	def GetCursor(self, List, Pos, font):
		if time() % 1 > 0.5:
			List.append((self.fonts[font].Cursor, Pos))
		return List

	def GetInputTextPos(self):
		BoardX, BoardY = self.Dimensions['BoardCentre']
		GameX, GameY = self.Surfaces['Game'].centre
		return (BoardX, (BoardY + 50)) if self.PlayStarted else (GameX, (GameY + 100))

	def BuildInputText(self):
		ToBlit = []

		if self.UserInput.Text:
			ToBlit.append((Message := self.GetText(self.UserInput.Text, pos=self.GetInputTextPos())))
			self.GetCursor(ToBlit, Message[1].topright, 'Normal')
		else:
			self.GetCursor(ToBlit, self.GetInputTextPos(), 'Normal')

		return ToBlit

	def ColourTransition(self, colour1, colour2, OpacityTransition=False, TimeToTake=1000):
		"""Generator function for transitioning between either two colours or two opacity values"""

		if isinstance(colour1, str):
			colour1 = self.Colours[colour1]

		if isinstance(colour2, str):
			colour2 = self.Colours[colour2]

		if OpacityTransition:
			colour1, colour2 = [colour1], [colour2]

		StartTime = PreviousTime = GetTicks()
		EndTime = StartTime + TimeToTake
		CurrentColour = colour1
		Range = range(1) if OpacityTransition else range(3)

		while (CurrentTime := GetTicks()) < EndTime:
			Elapsed = CurrentTime - PreviousTime
			ColourStep = [(((colour2[i] - colour1[i]) / TimeToTake) * Elapsed) for i in Range]
			CurrentColour = [CurrentColour[i] + ColourStep[i] for i in Range]

			if any(CurrentColour[i] < 0 or CurrentColour[i] > 255 for i in Range):
				break

			PreviousTime = CurrentTime
			yield CurrentColour[0] if OpacityTransition else CurrentColour

		yield colour2[0] if OpacityTransition else colour2

	def Fade(self, colour1=None, colour2=None, FadeIn=True, TextFade=False,
	         CardFade=False, ScoreboardFade=False,
	         TimeToTake=1000, EndOfTrickFade=False):

		"""Function for fading cards, text or the board colour, either in or out"""

		if CardFade:
			colour1 = 255 if FadeIn else 0
			colour2 = 0 if FadeIn else 255
			if FadeIn:
				self.Queues.SurfaceUpdates.put(['TrumpCard', 'Hand'])

		elif ScoreboardFade:
			self.CurrentColours['Scoreboard'] = colour1

		elif TextFade and FadeIn:
			self.Queues.SurfaceUpdates.put(['Board', 'TrumpCard'])

		for step in self.ColourTransition(colour1, colour2, OpacityTransition=CardFade, TimeToTake=TimeToTake):
			if ScoreboardFade:
				self.CurrentColours['Scoreboard'] = step
				self.Queues.SurfaceUpdates.put(['Scoreboard'])
			elif TextFade:
				self.CurrentColours['Text'] = step
				self.Queues.SurfaceUpdates.put(['Board'])
			elif CardFade:
				if FadeIn:
					ToUpdate = ['Hand', 'TrumpCard']
					self.CoverRectOpacities['Hand'] = self.CoverRectOpacities['TrumpCard'] = step
				elif EndOfTrickFade:
					ToUpdate = ['Board']
					self.CoverRectOpacities['Board'] = step
				else:
					ToUpdate = ['TrumpCard']
					self.CoverRectOpacities['TrumpCard'] = step

				self.Queues.SurfaceUpdates.put(ToUpdate)
			else:
				self.CurrentColours['Game'] = step
				if not FadeIn:
					self.CurrentColours['Scoreboard'] = step
					self.Queues.SurfaceUpdates.put(['Scoreboard'])

		self.Queues.SurfaceUpdates.put(['Board', 'TrumpCard', 'Hand'])

	def InteractiveScoreboard(self):
		pg.mouse.set_cursor(*self.Cursors['Wait'])
		fig, ax = plt.subplots()

		# hide axes
		ax.axis('off')
		ax.axis('tight')
		plt.rc('font', family='Times New Roman')

		fig.canvas.set_window_title('Knock scoreboard')
		fig.patch.set_facecolor('xkcd:scarlet')

		names = [f'{player}' for player in self.gameplayers]

		PlayerNoTimes4 = self.PlayerNumber * 4
		columnNo = PlayerNoTimes4 + 2
		columns = ['', ''] + sum((['', name, '', ''] for name in names), start=[])

		FirstLine = ['Round', 'Cards'] + sum((['Bid', 'Won', 'Points', 'Score'] for name in names), start=[])

		StartNo = self.Attributes.StartCardNumber
		RoundsPlayed = self.ClientSideAttributes['RoundNumber'] - 1

		Data = [FirstLine] + self.gameplayers.Scoreboard + [
			([x, y] + [None for c in range(PlayerNoTimes4)])
			for x, y in zip(range((RoundsPlayed + 1), (StartNo + 1)), range((StartNo - RoundsPlayed), 0, -1))
		]

		df = pd.DataFrame(Data, columns=columns)

		table = ax.table(
			cellText=df.values,
			colLabels=df.columns,
			loc='center',
			cellLoc='center',
			colColours=['none' for column in columns]
		)

		table.auto_set_font_size(False)

		for i, string in zip(range(2), ('B', 'BR')):
			table[0, i].visible_edges = string

		for (i, name), (j, string) in product(enumerate(names), zip(range(2, 6), ('TBL', 'TB', 'TB', 'TBR'))):
			table[0, ((i * 4) + j)].visible_edges = string

		for i in range(columnNo):
			table[1, i].set_facecolor(f'xkcd:burnt siena')

			for j in range(2):
				table[j, i].set_text_props(fontweight='bold')

		for i in range(2, (len(Data) + 1)):
			for j in range(2):
				table[i, j].set_text_props(fontweight='bold')
				table[i, j].set_facecolor(f'xkcd:{"dark beige" if i % 2 else "pale brown"}')

			for j in range(2, columnNo):
				if (j - 1) % 4:
					colour = "very light green" if i % 2 else "very light blue"
				else:
					try:
						Max = max(int(table[i, x].get_text().get_text()) for x in range(5, columnNo, 4))
						assert int(table[i, j].get_text().get_text()) == Max
						colour = "periwinkle"
					except (ValueError, AssertionError):
						colour = 'baby blue'

				table[i, j].set_facecolor(f'xkcd:{colour}')

		ax.set_title('SCOREBOARD\n', fontname='Algerian', size=40)

		fig.tight_layout()

		manager = plt.get_current_fig_manager()
		manager.window.showMaximized()
		manager.window.setWindowIcon(QtGui.QIcon(r'CardImages\PyinstallerIcon.ico'))

		plt.show()
		return GetTicks()

	def InitialiseWindow(self, WindowDimensions, flags):
		display.set_caption('Knock (made by Alex Waygood)')
		display.set_icon(self.WindowIcon)
		self.Window = display.set_mode(WindowDimensions, flags=flags)

	def ZoomWindow(self, Button, ScreenSize):
		x, y = self.Dimensions['Window']

		if (self.Fullscreen and Button in (4, pg.K_PLUS)) or (Button in (5, pg.K_MINUS) and x == 10 and y == 10):
			return None

		a, b = ((x + 20), (y + 20)) if Button in (4, pg.K_PLUS) else ((x - 20), (y - 20))

		if a >= ScreenSize[0] and b >= ScreenSize[1]:
			self.Fullscreen = True

			with self.lock:
				self.RedrawWindow(ToFullScreen=True)

			return None

		FromFullScreen = self.Fullscreen
		self.Fullscreen = False
		x, ResizeNeeded1 = ResizeHelper(a, x, ScreenSize, 0)
		y, ResizeNeeded2 = ResizeHelper(b, y, ScreenSize, 1)

		if ResizeNeeded1 or ResizeNeeded2:
			with self.lock:
				self.RedrawWindow(WindowDimensions=(x, y), FromFullScreen=FromFullScreen)

	def UpdateAttributesWithLock(self):
		with self.lock:
			self.UpdateGameAttributes()

	def MouseSetter(self):
		MousePos = pg.mouse.get_pos()
		Attrs = self.ClientSideAttributes
		Hand = self.player.Hand

		if self.Scrollwheel.IsDown:
			DownX, DownY, MouseX, MouseY = *self.Scrollwheel.DownPos, *MousePos
			if MouseX < (DownX - 50):
				if MouseY < (DownY - 50):
					cur = 'NW'
				elif MouseY > (DownY + 50):
					cur = 'SW'
				else:
					cur = 'W'
			elif MouseX > (DownX + 50):
				if MouseY < (DownY - 50):
					cur = 'NE'
				elif MouseY > (DownY + 50):
					cur = 'SE'
				else:
					cur = 'E'
			elif MouseY > (DownY + 50):
				cur = 'S'
			elif MouseY < (DownY - 50):
				cur = 'N'
			else:
				cur = 'Diamond'

		elif pg.mouse.get_pressed(5)[0] and pg.mouse.get_pressed(5)[2]:
			cur = 'Hand'

		elif Hand and Attrs['TrickInProgress'] and Attrs['WhoseTurnPlayerIndex'] == self.player.playerindex:
			cur = 'default'
			for card in Hand:
				if card.colliderect.collidepoint(*MousePos):
					self.CardHoverID = f'{card}'
					cur = 'Hand'

					if PlayedCards := self.Attributes.PlayedCards:
						SuitLed = PlayedCards[0].Suit
						Condition = any(UnplayedCard.Suit == SuitLed for UnplayedCard in Hand)

						if card.Suit != SuitLed and Condition:
							cur = 'IllegalMove'
		else:
			cur = 'default'

		self.cur = cur
		pg.mouse.set_cursor(*self.Cursors[cur])
		
	def AddInputText(self, event):
		if not (Input := self.UserInput.AddInputText(event)):
			return None

		if isinstance(self.name, int):
			if len(Input) < 30:
				# Don't need to check that letters are ASCII-compliant;
				# wouldn't have been able to type them if they weren't.
				self.name = Input
				self.Queues.ServerComms.put(('player', Input))
			else:
				self.Errors.ThisPass.append('Name must be <30 characters; please try again.')

		elif not (self.Attributes.StartCardNumber or self.player.playerindex):
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			try:
				assert 1 <= float(Input) <= self.MaxCardNumber and float(Input).is_integer()
				self.game.Attributes.StartCardNumber = int(Input)
				self.Queues.ServerComms.put(('CardNumber', Input))
			except:
				self.Errors.ThisPass.append(f'Please enter an integer between 1 and {self.MaxCardNumber}')

		elif self.player.Bid == -1:
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			Count = len(self.player.Hand)

			try:
				assert 0 <= float(Input) <= Count and float(Input).is_integer()
				self.game.PlayerMakesBid(Input, player=self.player)
				self.Queues.ServerComms.put(('Bid', Input))
			except:
				self.Errors.ThisPass.append(f'Your bid must be an integer between 0 and {Count}.')
				
	def ExecutePlay(self):
		self.game.ExecutePlay(self.CardHoverID, self.player.playerindex)
		self.UpdateAttributesWithLock()
		self.Queues.ServerComms.put(('PlayCard', self.CardHoverID))

	def FireworkDisplay(self):
		# FIREWORK LOOP (adapted from code by Adam Binks)
		x, y = self.Dimensions['Window']
		dt = self.clock.tick(self.FireworkSettings['FPS']) / 60.0

		# every frame blit a low alpha black surf so that all effects fade out slowly
		self.BlitSurface('Game', 'blackSurf')

		if (self.FireworkVars.LastFirework + self.FireworkVars.RandomAmount) < (Time := GetTicks()) < (self.FireworkVars.EndTime - 6000):
			Choice = random.choice((True, False))

			if Choice:
				Sparker(
					pos=(random.randint(0, x), random.randint(0, y)),
					colour=(random.uniform(0, 255), random.uniform(0, 255), random.uniform(0, 255)),
					velocity=random.uniform(40, 60),
					particleSize=random.uniform(10, 20),
					sparsity=random.uniform(0.05, 0.15),
					hasTrail=True,
					lifetime=random.uniform(10, 20),
					WindowDimensions=self.Dimensions['Window'],
					isShimmer=False
				)
			else:
				Sparker(
					pos=(random.randint(0, x), random.randint(0, y)),
					colour=(random.uniform(50, 255), random.uniform(50, 255), random.uniform(50, 255)),
					velocity=random.uniform(1, 2),
					particleSize=random.uniform(3, 8),
					sparsity=random.uniform(0.05, 0.15),
					hasTrail=False,
					lifetime=random.uniform(20, 30),
					isShimmer=True,
					radius=random.uniform(40, 100),
					proportion=0.6,
					focusRad=random.choice((0, 0.4, 3, 6)),
					WindowDimensions=self.Dimensions['Window'],
					weight=random.uniform(0.001, 0.0015)
				)

			self.FireworkVars.LastFirework = Time
			self.FireworkVars.RandomAmount = random.randint(*self.FireworkSettings['Bounds'])

		for item in chain(Particle.allParticles, Sparker.allSparkers):
			item.update(dt)
			item.draw(self.Surfaces['Game'])

	def ErrorMessages(self):
		self.Errors.StartTime = GetTicks()

		if not self.Errors.Messages:
			if not self.Errors.Title:
				self.Errors.Title = self.GetText(f'Messages to {self.name}:', 'Title', pos=self.Errors.Pos)

			self.Errors.Messages = [self.Errors.Title]
			y = self.Errors.Pos[1] + self.fonts['Title'].linesize

		else:
			y = self.Errors.Messages[-1][1].y + self.fonts['Normal'].linesize

		x = self.Errors.Pos[0]

		for Error in self.Errors.ThisPass:
			self.Errors.Messages.append(self.GetText(Error, 'Normal', pos=(x, y)))
			y += self.fonts['Normal'].linesize

	def HandleClicks(self):
		if self.Contexts.Input.ClickToStart:
			self.game.StartPlay = True
			self.Queues.ServerComms.put('StartGame')

		elif self.cur == 'Hand' and self.player.PosInTrick == len(self.Attributes.PlayedCards):
			self.ExecutePlay()

	def StandardScreenBuild(self):
		self.clock.tick(100)
		self.Fill(self.Window, CurrentColour=True)
		self.Fill('Game', CurrentColour=True)
		InputTextBlits = self.BuildInputText() if self.Contexts.Input.TypingNeeded else []
		self.Typewriter.RenderStepsIfNeeded(self.fonts['Title'])
		TypewriterCentre = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Surfaces['Game'].centre

		if TypewrittenText := self.Typewriter.GetTypedText(TypewriterCentre):
			self.GetCursor(TypewrittenText, TypewrittenText[0][1].topright, 'Title')

		if self.Contexts.Input.Message:
			Messages = [self.GetText(self.Contexts.Input.Message, font=self.Contexts.Input.font)]
		else:
			Messages = []

		ToUpdate = []

		while not self.Queues.SurfaceUpdates.empty():
			ToUpdate += [self.Queues.SurfaceUpdates.get()]

		self.UpdateSurfaces(ToUpdate=ToUpdate)

		self.BlitSurface(
			'Game',
			chain(self.SurfacesOnScreen, TypewrittenText, Messages, InputTextBlits, self.Errors.Messages)
		)

		self.BlitSurface(self.Window, 'Game')
		self.MouseSetter()

	def HandleEvent(self, event):
		GameSurf = self.Surfaces['Game']
		ScreenSize = self.Dimensions['ScreenSize']

		if (EvType := event.type) == pg.QUIT:
			self.QuitGame()

		elif EvType == pg.KEYDOWN:
			if (EvKey := event.key) == pg.K_TAB or (EvKey == pg.K_ESCAPE and self.Fullscreen):
				self.DeactivateVideoResize = True

				with self.lock:
					self.RedrawWindow(GameSurf, FromFullScreen=self.Fullscreen, ToFullScreen=(not self.Fullscreen))

				self.Fullscreen = not self.Fullscreen

			elif key.get_mods() & pg.KMOD_CTRL:
				if EvKey == pg.K_q:
					self.QuitGame()

				elif EvKey == pg.K_t and self.PlayStarted and not self.Contexts.Input.FireworksDisplay:
					self.InteractiveScoreboard()

				elif EvKey == pg.K_c:
					self.GameSurfMove('centre', None)

				elif EvKey in (pg.K_PLUS, pg.K_MINUS):
					self.ZoomWindow(EvKey, ScreenSize)

			elif self.Contexts.Input.GameReset and EvKey in (pg.K_SPACE, pg.K_RETURN):
				self.game.RepeatGame = True
				self.Queues.ServerComms.put('1')

			elif not self.Contexts.Input.FireworksDisplay and EvKey in (pg.K_UP, pg.K_DOWN, pg.K_RIGHT, pg.K_LEFT):
				self.GameSurfMove('arrow', EvKey)

			elif self.Contexts.Input.TypingNeeded:
				self.AddInputText(event)

		elif EvType == pg.VIDEORESIZE:
			# Videoresize events are triggered on exiting/entering fullscreen as well as manual resizing;
			# we only want it to be triggered after a manual resize.

			if self.DeactivateVideoResize:
				self.DeactivateVideoResize = False
			else:
				with self.lock:
					self.RedrawWindow(WindowDimensions=event.size)

		elif EvType == pg.MOUSEBUTTONDOWN:
			Button = event.button

			if Button == 1 and self.Contexts.Input.ClicksNeeded() and not pg.mouse.get_pressed(5)[2]:
				self.UserInput.click = True

			elif Button == 2 and not self.Contexts.Input.FireworksDisplay:
				self.Scrollwheel.clicked(pg.mouse.get_pos(), GetTicks())

			elif Button in (4, 5):
				if key.get_mods() & pg.KMOD_CTRL:
					self.ZoomWindow(Button, ScreenSize)
				elif not self.Contexts.Input.FireworksDisplay:
					self.GameSurfMove('arrow', (pg.K_UP if Button == 4 else pg.K_DOWN))

		elif not self.Contexts.Input.FireworksDisplay:
			if EvType == pg.MOUSEBUTTONUP:
				if (Button := event.button) == 1:
					self.UserInput.click = False
				elif Button == 2 and GetTicks() > self.Scrollwheel.OriginalDownTime + 1000:
					self.Scrollwheel.IsDown = False

			elif EvType == pg.MOUSEMOTION and pg.mouse.get_pressed(5)[0] and pg.mouse.get_pressed(5)[2]:
				self.GameSurfMove('mouse', event.rel)


print('Welcome to Knock!')
# IP = 'alexknockparty.mywire.org'
IP = '127.0.0.1'
print('Connecting to local host.')
Port = 5555

# IP = inputCustom(IPValidation, 'Please enter the IP address or hostname of the server you want to connect to: ')
# Port = inputInt('Please enter which port you wish to connect to: ', min=5000, max=65535)

password = inputCustom(
	PasswordInput,
	'Please enter the password to connect to this game, if one has been set (press Enter if none has been set): ',
	blank=True
)

ThemeChoices = ['Classic theme (dark red board)', 'High contrast theme ()']
ThemeDict = {'Classic theme (dark red board)': 'Classic', 'High contrast theme ()': 'High Contrast'}

Theme = inputMenu(
	choices=ThemeChoices,
	prompt='Please select the colour theme you would like to play with:\n\n',
	numbered=True
)

Theme = ThemeDict[Theme]

print('Initialising...')

try:
	# Try to calculate the size of the client's computer screen
	from screeninfo import get_monitors
	Monitor = get_monitors()[0]
	WindowDimensions = (WindowX, WindowY) = (Monitor.width, Monitor.height)
except:
	WindowDimensions = (WindowX, WindowY) = (1300, 680)

_, NewCardDimensions, RequiredResizeRatio = GetDimensions1(WindowDimensions)

CardIDs = [f'{p[0]}{p[1]}' for p in product(chain(range(2, 11), ('J', 'Q', 'K', 'A')), ('♢', '♠', '♣', '♡'))]
CardImages = {CardID: Image.open(path.join('CardImages', f'{CardID}.jpg')).convert("RGB") for CardID in CardIDs}

CardImages = {
	key: value.resize((int(value.size[0] / RequiredResizeRatio), int(value.size[1] / RequiredResizeRatio)))
	for key, value in CardImages.items()
}

with printing_exc():
	KnockTournament(WindowDimensions, NewCardDimensions, CardImages, IP, Port, password, Theme)
