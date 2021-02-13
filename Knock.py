#! Python3

"""This is the client-side script, that should be run by each player who wants to take part in the game."""


import sys, random, traceback

import pandas as pd
import matplotlib.pyplot as plt

from FireworkParticle import Particle
from FireworkSparker import Sparker
from Network import Network
from PasswordChecker import PasswordInput
from ServerUpdaters import Triggers, AttributeTracker
from PygameWrappers import SurfaceAndPosition, CoverRect, CoverRectList, FontAndLinesize, RestartDisplay
from Card import Card
from GameSurface import GameSurface
from Cursors import CursorDict

from HelperFunctions import GetTime, PrintableCharactersPlusSpace, GetDimensions1, \
	ResizeHelper, Action, OpenableObject, MessageHolder

from time import time
from PIL import Image
from os import chdir, environ, path
from itertools import chain, accumulate, product
from threading import Thread, Lock
from pyinputplus import inputCustom, inputYesNo
from fractions import Fraction
from queue import Queue
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
from pygame.font import SysFont


# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
if getattr(sys, 'frozen', False):
	chdir(sys._MEIPASS)
	filterwarnings("ignore")


class KnockTournament(object):
	"""

	Main object which contains the vast majority of the code for visualising the game on the client side.
	This object's methods also handle keyboard/mouse inputs, and various animations that happen throughout.

	"""

	__slots__ = 'GameUpdatesNeeded', 'Triggers', 'fonts', 'gameplayers', 'Attributes', 'player', 'ToBlit', \
	            'InputText', 'Client', 'game', 'Window', 'CardImages', 'Surfaces', 'PlayStarted', \
	            'ScoreboardAttributes', 'clock', 'PlayerTextPositions', 'name', 'Dimensions', 'Errors', \
	            'ServerCommsQueue', 'ClientSideAttributes', 'PlayerNumber', 'MaxCardNumber', 'StartCardPositions', \
	            'BaseCardImages', 'CurrentColours', 'DeactivateVideoResize', 'ScrollwheelDown', 'Fullscreen', \
	            'ScrollwheelDownPos', 'ScrollwheelDownTime', 'OriginalScrollwheelDownTime', 'WindowIcon', \
	            'TopLeftPartial', 'InteractiveScoreboardRequest', 'SurfacesOnScreen', 'lock', 'CardFadesInProgress',\
	            'CoverRectOpacities', 'FireworksInProgress', 'ClicksNeeded', 'TypingNeeded', 'GameReset', \
	            'ClickToStart', 'UserInputQ', 'InputTextBlits', 'PreviousInputText', 'MessagesOnScreen', \
	            'FunctionDict', 'GameSurfMovementDict', 'cur', 'CardHoverID', 'TypewriterEvents', \
	            'RenderedTypewriterSteps', 'TypewrittenText', 'TypewriterRect'

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
		'LightGrey': (128, 128, 128),
		'Black_fade': (0, 0, 0, FireworkSettings['FadeRate'])
	}

	DefaultTextColour = (0, 0, 0)
	DefaultFillColour = Colours['Maroon']

	Cursors = CursorDict

	def __init__(self, WindowDimensions, StartCardDimensions, CardImages, IP, Port, password):
		self.ServerCommsQueue = Queue()
		self.ScoreboardAttributes = {}
		self.PreviousInputText = ''
		self.InputText = ''
		self.GameUpdatesNeeded = OpenableObject()
		self.PlayStarted = False
		self.DeactivateVideoResize = False
		self.ScrollwheelDown = False
		self.ScrollwheelDownPos = ()
		self.ScrollwheelDownTime = 0
		self.OriginalScrollwheelDownTime = 0
		self.Fullscreen = True
		self.InputTextBlits = []
		self.lock = Lock()
		self.SurfacesOnScreen = []
		self.Attributes = AttributeTracker()
		self.InteractiveScoreboardRequest = False
		self.FireworksInProgress = False
		self.ClicksNeeded = OpenableObject()
		self.TypingNeeded = OpenableObject()
		self.GameReset = OpenableObject()
		self.ClickToStart = OpenableObject()
		self.MessagesOnScreen = MessageHolder()
		self.UserInputQ = Queue()
		self.TypewriterEvents = Queue()
		self.cur = ''
		self.CardHoverID = ''
		self.RenderedTypewriterSteps = []
		self.TypewrittenText = -1
		self.TypewriterRect = None

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

		self.Errors = {
			'Messages': [],
			'ThisPass': [],
			'Title': None
		}

		self.Triggers = {
			'Client': Triggers(),
			'Server': Triggers()
		}

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

		self.CardFadesInProgress = {
			'Hand': OpenableObject(),
			'TrumpCard': OpenableObject(),
			'Board': OpenableObject
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
				self.game, self.player = self.Client.InfoDict['game'], self.Client.InfoDict['player']
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
		self.Fill('Cursor', 'Black')
		self.UpdateGameAttributes()

		GameSurf = self.Surfaces['Game']

		self.FunctionDict = {
			'mouse': lambda x: self.MouseSetter(),
			'quit': lambda x: 'quit',
			'GameSurfMove': lambda x: self.GameSurfMove(*x),
			'scrollwheelvars': lambda x: self.NewScrollwheelVars(),
			'scrollwheelup': lambda x: self.ScrollwheelUp(),
			'inputtext': lambda x: self.AddInputText(x),
			'ExecutePlay': lambda x: self.ExecutePlay()
		}

		self.GameSurfMovementDict = {
			'arrow': lambda x: GameSurf.ArrowKeyMove(x),
			'mouse': lambda x: GameSurf.MouseMove(x),
			'centre': lambda x: GameSurf.MoveToCentre(),
			'scrollwheel': lambda x: GameSurf.ScrollwheelDownMove(x)
		}

		print(f'Game display now initialising at {GetTime()}...')
		Thread(target=self.ThreadedGameUpdate).start()
		Thread(target=self.EventHandler).start()
		self.Errors['StartTime'] = GetTicks()
		Thread(target=self.PlayTournament).start()

		while True:
			self.HandleEvents()

	def PlayTournament(self):
		# Menu sequence

		with self.TypingNeeded, self.MessagesOnScreen('Please enter your name', 'Massive'):
			while isinstance(self.name, int):
				pass

		while not self.ServerCommsQueue.empty():
			pass

		delay(100)

		Args = ('Waiting for all players to connect and enter their names', 'Massive')
		with self.GameUpdatesNeeded, self.MessagesOnScreen(*Args):
			while not self.gameplayers.AllPlayersHaveJoinedTheGame():
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
			self.TypeWriterText(Message, WaitAfterwards=1000)

		if self.player.playerindex and GamesPlayed:
			text = f"Waiting for {self.gameplayers[0]} to decide how many cards the game will start with."

		elif self.player.playerindex:
			text = f"As the first player to join this game, it is {self.gameplayers[0]}'s " \
			       f"turn to decide how many cards the game will start with."

		elif GamesPlayed:
			Message2 = 'Your turn to decide the starting card number!'
			self.TypeWriterText(Message2)
			text = "Please enter how many cards you wish the game to start with:"

		else:
			text = "As the first player to join this game, it is your turn to decide " \
			       "how many cards you wish the game to start with:"

		self.TypeWriterText(text, WaitAfterwards=0)

		with self.GameUpdatesNeeded, self.MessagesOnScreen(text, 'Title'):
			self.TypingNeeded.value = not self.player.playerindex
			while not self.Attributes.StartCardNumber:
				pass
			self.TypingNeeded.value = False

		# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
		self.CalculateHandRects(
			self.Surfaces['Game'].RectWidth,
			self.Dimensions['WindowMargin'],
			self.Dimensions['Card'][0]
		)

		self.TypeWriterText('Click to start the game for all players!', WaitAfterwards=0)
		Clicks, GameUpdates, Click2Start = self.ClicksNeeded, self.GameUpdatesNeeded, self.ClickToStart
		Messages = self.MessagesOnScreen

		with Clicks, GameUpdates, Click2Start, Messages('Click to start the game for all players!', 'Title'):
			while not self.game.StartPlay:
				pass

		if not GamesPlayed:
			self.Fade(colour1='LightGrey', colour2='Maroon')

		self.SurfacesOnScreen.append('Scoreboard')
		self.Fade(colour1='Maroon', colour2='LightGrey', ScoreboardFade=True)
		self.ServerCommsQueue.put('AC')
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
			self.TypeWriterText(m)

		if not GamesPlayed and RoundNumber == 1:
			Message = "Over the course of the game, your name will be underlined if it's your turn to play."
			Message2 = 'Press the Tab key at any time to toggle in and out of full-screen mode.'

			self.TypeWriterText(Message)
			self.TypeWriterText(Message2)

		# Wait for the server to make a new pack of cards.
		self.AttributeWait('NewPack')
		TrumpCard = self.Attributes.TrumpCard
		self.TypeWriterText(f'The trumpcard for this round is the {TrumpCard}, which has been removed from the pack.')

		# Wait for the server to deal cards for this round.
		self.AttributeWait('CardsDealt')

		# Fade in the *player text on the board only*, then the cards in your hand + the trumpcard.
		self.CurrentColours['Text'] = self.Colours['Maroon']

		for string in ('TrumpCard', 'Hand'):
			self.Surfaces[string].SetCoverRectOpacity(255)

		with self.CardFadesInProgress['TrumpCard'], self.CardFadesInProgress['Hand']:
			self.SurfacesOnScreen += ['Board', 'TrumpCard']
			self.Fade(colour1='Maroon', colour2=(0, 0, 0), FadeIn=True, TextFade=True)
			self.SurfacesOnScreen.append('Hand')
			self.Fade(CardFade=True, FadeIn=True)

		delay(250)

		if RoundNumber == 1 and not GamesPlayed:
			self.TypeWriterText('Cards for this round have been dealt; each player must decide what they will bid.')

		# We need to enter our bid.
		with self.GameUpdatesNeeded:
			with self.TypingNeeded, self.MessagesOnScreen('Please enter your bid:', 'Title'):
				while self.player.Bid == -1:
					pass

			# We now need to wait until everybody else has bid.
			i = self.player.playerindex

			while not self.gameplayers.AllBid():
				self.MessagesOnScreen.m = self.gameplayers.BidWaitingText(i)

			self.MessagesOnScreen.m = ''
			self.BlockingMessageToServer()

		# (Refresh the board.)
		self.UpdateAttributesWithLock()

		# Announce what all the players are bidding this round.
		for Message in self.gameplayers.BidText():
			self.TypeWriterText(Message)

		self.ServerCommsQueue.put('AC')

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
		self.ServerCommsQueue.put('AC')
		self.UpdateGameSurface()
		Text = f'{f"TRICK {TrickNumber} starting" if CardNumberThisRound != 1 else "TRICK STARTING"}:'
		self.TypeWriterText(Text)

		# Make sure the server is ready for the trick to start.
		self.AttributeWait('TrickStart')

		# Tell the server we're ready to play the trick.
		self.BlockingMessageToServer('AC', UpdateWindowAfter=True)

		with self.GameUpdatesNeeded:
			# Play the trick, wait for all players to play.
			for i in range(PlayerNo):
				self.ClientSideAttributes['WhoseTurnPlayerIndex'] = PlayerOrder[i]

				while (CardsOnBoard := len(self.Attributes.PlayedCards)) == i:
					self.UpdateSurfaces(ToUpdate=('Board', 'Hand'))
					self.ClicksNeeded.value = (CardsOnBoard == Pos)

			self.ClicksNeeded.value = False
			self.AttributeWait('TrickWinnerLogged')

		PlayedCards, trumpsuit = self.Attributes.PlayedCards, self.Attributes.trumpsuit
		WinningCard = max(PlayedCards, key=lambda card: card.GetWinValue(PlayedCards[0].ActualSuit, trumpsuit))
		(Winner := self.gameplayers[WinningCard.PlayedBy]).WinsTrick()

		# Tell the server we've logged the winner
		self.ServerCommsQueue.put('AC')

		if TrickNumber != CardNumberThisRound:

			self.ClientSideAttributes.update({
				'WhoseTurnPlayerIndex': -1,
				'TrickInProgress': False
			})

			self.UpdateGameAttributes()

		delay(500)
		Text = f'{Winner} won {f"trick {TrickNumber}" if CardNumberThisRound != 1 else "the trick"}!'
		self.TypeWriterText(Text)

		# Fade out the cards on the board
		with self.CardFadesInProgress['Board']:
			self.Fade(FadeIn=False, CardFade=True, TimeToTake=300, EndOfTrickFade=True)
			self.Attributes.PlayedCards.clear()

		self.UpdateGameSurface(ToUpdate=('Board',))

		if TrickNumber != CardNumberThisRound:
			self.ServerCommsQueue.put('AC')

		return Winner.playerindex

	def EndRound(self, FinalRound: bool):
		self.BuildScoreboard('LightGrey')
		self.BlitSurface('Game', 'Scoreboard')

		# Fade out the trumpcard, then the text on the board
		self.Surfaces['TrumpCard'].SetCoverRectOpacity(0)

		with self.CardFadesInProgress['TrumpCard']:
			self.Fade(FadeIn=False, CardFade=True)
			self.Attributes.TrumpCard = None
			self.Fade(colour1=(0, 0, 0), colour2='Maroon', FadeIn=False, TextFade=True)

			for string in ('Board', 'TrumpCard'):
				self.SurfacesOnScreen.remove(string)

		self.CardFadesInProgress['TrumpCard'] = False
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
		self.ServerCommsQueue.put('AC')

		delay(500)

		for message in self.gameplayers.EndRoundText(FinalRound=FinalRound):
			self.TypeWriterText(message)

		self.ServerCommsQueue.put('AC')

	def EndGame(self, GamesPlayed):
		self.SurfacesOnScreen.remove('Hand')

		# Announce the final scores + who won the game.
		for text in self.gameplayers.GameCleanUp():
			self.TypeWriterText(text)

		self.PlayStarted = False
		delay(500)

		# Fade the screen out incrementally to prepare for the fireworks display
		self.Fade(colour1='LightGrey', colour2='Maroon', ScoreboardFade=True)
		self.Fade(colour1='Maroon', colour2=(0, 0, 0), FadeIn=False)
		self.SurfacesOnScreen.clear()

		self.FireworksDisplay()

		# Fade the screen back to maroon after the fireworks display.
		self.Fade(colour1=(0, 0, 0), colour2='Maroon')
		delay(1000)

		# Announce who's currently won the most games in this tournament so far.
		if GamesPlayed:
			for text in self.gameplayers.TournamentLeaders():
				self.TypeWriterText(text)

		Message = 'Press the spacebar to play again with the same players, or close the window to exit the game.'
		self.TypeWriterText(Message, WaitAfterwards=0)

		with self.GameReset, self.GameUpdatesNeeded, self.TypingNeeded:
			self.AttributeWait('NewGameReset')

		self.game.NewGameReset()
		self.gameplayers.NewGame()
		self.player.ResetPlayer(self.PlayerNumber)
		self.Surfaces['BaseScoreboard'] = None
		self.ServerCommsQueue.put('AC')
		self.Surfaces['Hand'].ClearRectList()
		self.ClientSideAttributes['RoundNumber'] = 1

	def FireworksDisplay(self):
		# This part of the code adapted from code by Adam Binks

		# every frame blit a low alpha black surf so that all effects fade out slowly
		Duration = self.FireworkSettings['SecondsDuration'] * 1000
		StartTime = LastFirework = GetTicks()
		EndTime = StartTime + Duration
		RandomAmount = random.randint(*self.FireworkSettings['Bounds'])
		x, y = self.Dimensions['Window']
		self.FireworksInProgress = True

		# FIREWORK LOOP (adapted from code by Adam Binks)
		while (Time := GetTicks()) < EndTime or Particle.allParticles:
			dt = self.clock.tick(self.FireworkSettings['FPS']) / 60.0
			self.BlitSurface('Game', 'blackSurf')
			self.BlitSurface(self.Window, 'Game')

			if (LastFirework + RandomAmount) < Time < (EndTime - 6000):
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

				LastFirework = Time
				RandomAmount = random.randint(*self.FireworkSettings['Bounds'])

			for item in chain(Particle.allParticles, Sparker.allSparkers):
				item.update(dt)
				item.draw(self.Surfaces['Game'])

		self.FireworksInProgress = False

	def ThreadedGameUpdate(self):
		"""This method runs throughout gameplay on a separate thread."""

		while True:
			while not self.ServerCommsQueue.empty():
				if isinstance((message := self.ServerCommsQueue.get()), str):
					self.GetGame(message)
				else:
					self.SendToServer(*message)
			if self.GameUpdatesNeeded:
				self.GetGame()

	def EventHandler(self):
		while True:
			if not self.UserInputQ.empty():
				i = self.UserInputQ.get()
				if self.FunctionDict[i.Type](i.args) == 'quit':
					break

	def BlockingMessageToServer(self, message='', UpdateWindowAfter=False):
		Q = self.ServerCommsQueue

		if message:
			Q.put(message)

		while not Q.empty():
			delay(1)

		if UpdateWindowAfter:
			self.UpdateGameAttributes(UpdateWindowAfter=True)

	def Fill(self, SurfaceObject, colour=None, CurrentColour=False):
		if CurrentColour:
			return self.Fill(
				SurfaceObject,
				self.CurrentColours['Scoreboard' if SurfaceObject == 'Scoreboard' else 'Game']
			)

		if isinstance(SurfaceObject, str):
			SurfaceObject = self.Surfaces[SurfaceObject]

		if colour and isinstance(colour, str):
			colour = self.Colours[colour]

		SurfaceObject.fill(colour)
		return SurfaceObject

	def GetPlayer(self):
		return self.game.gameplayers[self.name]

	def UpdateGameAttributes(self, UpdateWindowAfter=False):
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
		self.Triggers['Server'] = self.game.Triggers

		# This option should only be used if this method is being used by the main thread.
		# Pygame doesn't take well to being used in multiple threads simultaneously.
		if UpdateWindowAfter:
			self.UpdateGameSurface(ToUpdate=('Board',))

	def ReceiveGame(self, GameFromServer):
		if GameFromServer != self.game:
			self.game = GameFromServer
			if self.ServerCommsQueue.empty():
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

		CardImages = {
			ID: pg.transform.rotozoom(cardimage, 0, (1 / ResizeRatio))
			for ID, cardimage in self.BaseCardImages.items()
		}

		ErrorPos = (int(GameX * Fraction(550, 683)), int(GameY * Fraction(125, 192)))

		x = 10
		NormalFont = SysFont(self.DefaultFont, x, bold=True)
		UnderLineFont = SysFont(self.DefaultFont, x, bold=True)

		while x < 19:
			x += 1
			font = SysFont(self.DefaultFont, x, bold=True)
			font2 = SysFont(self.DefaultFont, x, bold=True)
			Size = font.size('Trick not in progress')

			if Size[0] > int(GameX * Fraction(70, 683)) or Size[1] > int(GameY * Fraction(18, 768)):
				break

			NormalFont = font
			UnderLineFont = font2

		x -= 1
		UnderLineFont.set_underline(True)

		fonts = {
			'Normal': FontAndLinesize(NormalFont),
			'UnderLine': FontAndLinesize(UnderLineFont),
			'Title': FontAndLinesize(SysFont(self.DefaultFont, 20, bold=True)),
			'Massive': FontAndLinesize(SysFont(self.DefaultFont, 40, bold=True))
		}

		BoardWidth = GameX // 2
		BoardMid = BoardWidth // 2
		BoardPos = [(GameX // 4), WindowMargin]
		BoardHeight = min(BoardWidth, (GameY - BoardPos[1] - (CardY + 40)))
		BoardFifth = BoardHeight // 5

		BoardCentre = (BoardWidth, ((BoardHeight // 2) + WindowMargin))

		NormalLinesize = fonts['Normal'].linesize
		TripleLinesize = 3 * NormalLinesize
		TwoFifthsBoard, ThreeFifthsBoard = (BoardFifth * 2), (BoardFifth * 3)

		PlayerTextPositions = (
			# Player1 - topleft
			(CardX, int(TwoFifthsBoard - TripleLinesize)),

			# Player2 = topmid
			(BoardMid, (NormalLinesize // 2)),

			# Player3 - topright
			((BoardWidth - CardX), int(TwoFifthsBoard - TripleLinesize)),

			# Player4 = bottomright
			((BoardWidth - CardX), ThreeFifthsBoard),

			# Player5 - bottommid
			(BoardMid, int(BoardHeight - (NormalLinesize * 5))),

			# Player6 - bottomleft
			(CardX, ThreeFifthsBoard)
		)

		HalfCardWidth, DoubleCardWidth = (CardX // 2), (CardX * 2)

		CardRectsOnBoard = (
			# Player1 - topleft
			((CardX + HalfCardWidth), (PlayerTextPositions[0][1] - HalfCardWidth)),

			# Player2 = topmid
			((BoardMid - HalfCardWidth), (PlayerTextPositions[1][1] + (NormalLinesize * 4))),

			# Player3 - topright
			((BoardWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[2][1] - HalfCardWidth)),

			# Player4 = bottomright
			((BoardWidth - (DoubleCardWidth + 60)), (PlayerTextPositions[3][1] - HalfCardWidth)),

			# Player5 - bottommid
			((BoardMid - HalfCardWidth), (PlayerTextPositions[4][1] - CardY - NormalLinesize)),

			# Player6 - bottomleft
			(DoubleCardWidth, (PlayerTextPositions[5][1] - HalfCardWidth))
		)

		TrumpCardSurfaceDimensions = ((CardX + 2), (CardY + int(NormalLinesize * 2.5) + 10))
		TrumpCardPos = (1, int(NormalLinesize * 2.5))
		SurfaceAndPosition.AddDefaults(NewCardDims, self.DefaultFillColour)

		Surfs = {
			'Cursor': pg.Surface((3, NormalLinesize)),

			'Scoreboard': SurfaceAndPosition(
				'Scoreboard',
				SurfaceDimensions=None,
				position=[WindowMargin, WindowMargin],
				FillColour=self.CurrentColours['Scoreboard']
			),

			'TrumpCard': SurfaceAndPosition(
				'TrumpCard',
				SurfaceDimensions=TrumpCardSurfaceDimensions,
				position=[(GameX - (CardX + 50)), WindowMargin],
				RectList=(TrumpCardPos,),
				Dimensions=TrumpCardSurfaceDimensions,
				CoverRectOpacity=self.CoverRectOpacities['TrumpCard']
			),

			'Hand': SurfaceAndPosition(
				'Hand',
				SurfaceDimensions=(GameX, (CardY + WindowMargin)),
				position=[0, (GameY - (CardY + WindowMargin))],
				CoverRectOpacity=self.CoverRectOpacities['Hand']
			),

			'Board': SurfaceAndPosition(
				'Board',
				SurfaceDimensions=(GameX, GameX),
				position=BoardPos.copy(),
				RectList=CardRectsOnBoard,
				CoverRectOpacity=self.CoverRectOpacities['Board']
			),

			'blackSurf': SurfaceAndPosition(
				'blackSurf',
				SurfaceDimensions=self.Dimensions['ScreenSize'],
				position=[0, 0],
				OpacityRequired=True,
				FillColour=self.Colours['Black_fade']
			)
		}

		# If we're calling it from Init, the Surfaces dict won't be formed yet,
		# so calling bool() as below will result in Key Error.
		HandRectsNeeded = False if FromInit else bool(self.Surfaces['Hand'].RectList)

		self.CardImages = CardImages
		self.Errors['Pos'] = ErrorPos
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

		self.UpdateSurfaces(ToUpdate=('Scoreboard', 'Hand', 'TrumpCard', 'Board'))

		for string in ('Hand', 'TrumpCard', 'Board'):
			if self.CardFadesInProgress[string]:
				self.BlitSurface(string, self.Surfaces[string].CoverRects)

	def CalculateHandRects(self, GameSurfX, WindowMargin, CardX):
		x = WindowMargin
		DoubleWindowMargin = x * 2
		StartNumber = self.Attributes.StartCardNumber
		PotentialBuffer = CardX // 2

		if ((CardX * StartNumber) + DoubleWindowMargin + (PotentialBuffer * (StartNumber - 1))) < GameSurfX:
			CardBufferInHand = PotentialBuffer
		else:
			CardBufferInHand = min(x, ((GameSurfX - DoubleWindowMargin - (CardX * StartNumber)) // (StartNumber - 1)))

		self.Surfaces['Hand'].AddRectList(
			[((x + (i * (CardX + CardBufferInHand))), 0) for i in range(StartNumber)],
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
		self.UserInputQ.put(Action('quit', None))
		pg.quit()
		self.Client.CloseDown()
		raise Exception('Game has ended.')

	def GameSurfMove(self, Type, arg):
		if Type == 'scrollwheel':
			self.ScrollwheelDownTime = GetTicks()
			
		with self.lock:
			self.GameSurfMovementDict[Type](arg)
			self.UpdateGameAttributes()

	def HandleEvents(self):
		""" Main pygame event loop """

		Condition = (len(self.gameplayers) != self.PlayerNumber and self.game.StartPlay)

		if Condition or not display.get_init() or not display.get_surface():
			self.QuitGame()

		if not self.FireworksInProgress:
			self.clock.tick(600)
			self.Fill(self.Window, CurrentColour=True)
			self.Fill('Game', CurrentColour=True)
			InputTextBlits = self.BuildInputText() if self.TypingNeeded else []

			if not self.TypewriterEvents.empty():
				text = self.TypewriterEvents.get()
				self.TypewriterRect = pg.Rect((0, 0), self.fonts['Title'].size(text))

				self.RenderedTypewriterSteps = [
					self.fonts['Title'].render(step, False, (0, 0, 0)) for step in accumulate(text)
				]

			if self.TypewrittenText > -1:
				TypewrittenText = self.RenderedTypewriterSteps[self.TypewrittenText]
				self.TypewriterRect.center = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Surfaces[
					'Game'].centre
				SubRect = TypewrittenText.get_rect()
				SubRect.topleft = self.TypewriterRect.topleft
				TypewrittenText = [(TypewrittenText, SubRect)]
				self.GetCursor(TypewrittenText, SubRect.topright)
			else:
				TypewrittenText = []

			if self.MessagesOnScreen:
				Messages = [self.GetText(self.MessagesOnScreen.m, font=self.MessagesOnScreen.font)]
			else:
				Messages = []

			self.BlitSurface(
				'Game',
				chain(self.SurfacesOnScreen, TypewrittenText, Messages, InputTextBlits, self.Errors['Messages'])
			)

			self.BlitSurface(self.Window, 'Game')
			self.UserInputQ.put(Action('mouse', None))

		UpdateDisplay()
		self.Errors['ThisPass'].clear()
		click = False
		GameSurf = self.Surfaces['Game']
		ScreenSize = self.Dimensions['ScreenSize']

		for event in pg.event.get():
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

					elif EvKey == pg.K_t and self.PlayStarted and not self.FireworksInProgress:
						self.InteractiveScoreboard()

					elif EvKey == pg.K_c:
						self.UserInputQ.put(Action('GameSurfMove', ('centre', None)))

					elif EvKey in (pg.K_PLUS, pg.K_MINUS):
						self.ZoomWindow(EvKey, ScreenSize)

				elif self.GameReset and EvKey in (pg.K_SPACE, pg.K_RETURN):
					self.game.RepeatGame = True
					self.ServerCommsQueue.put('1')

				elif not self.FireworksInProgress and EvKey in (pg.K_UP, pg.K_DOWN, pg.K_RIGHT, pg.K_LEFT):
					self.UserInputQ.put(Action('GameSurfMove', ('arrow', EvKey)))

				elif self.TypingNeeded:
					self.UserInputQ.put(Action('inputtext', event))

			elif EvType == pg.VIDEORESIZE:
				# Videoresize events are triggered on exiting/entering fullscreen as well as manual resizing;
				# we only want it to be triggered after a manual resize.

				if self.DeactivateVideoResize:
					self.DeactivateVideoResize = False
				else:
					with self.lock:
						self.RedrawWindow(WindowDimensions=event.size)

			elif EvType == pg.MOUSEBUTTONDOWN:
				if (Button := event.button) == 1 and self.ClicksNeeded and not pg.mouse.get_pressed(5)[2]:
					click = True

				elif Button == 2 and not self.FireworksInProgress:
					self.UserInputQ.put(Action('scrollwheelvars', None))

				elif Button in (4, 5):
					if key.get_mods() & pg.KMOD_CTRL:
						self.ZoomWindow(Button, ScreenSize)
					elif not self.FireworksInProgress:
						self.UserInputQ.put(Action('GameSurfMove', ('arrow', (pg.K_UP if Button == 4 else pg.K_DOWN))))

			elif not self.FireworksInProgress:
				if EvType == pg.MOUSEBUTTONUP:
					if (Button := event.button) == 1:
						click = False
					elif Button == 2 and GetTicks() > self.OriginalScrollwheelDownTime + 1000:
						self.UserInputQ.put(Action('scrollwheelup', None))

				elif EvType == pg.MOUSEMOTION and pg.mouse.get_pressed(5)[0] and pg.mouse.get_pressed(5)[2]:
					self.UserInputQ.put(Action('GameSurfMove', ('mouse', event.rel)))

		if self.ScrollwheelDown and GetTicks() > (self.ScrollwheelDownTime + 20):
			self.UserInputQ.put(Action('GameSurfMove', ('scrollwheel', self.ScrollwheelDownPos)))

		if not self.TypingNeeded or self.ClicksNeeded:
			return None

		if click:
			if self.ClickToStart:
				self.game.StartPlay = True
				self.ServerCommsQueue.put('StartGame')

			elif self.cur == 'Hand' and self.player.PosInTrick == len(self.Attributes.PlayedCards):
				self.UserInputQ.put(Action('ExecutePlay', None))

		if self.Errors['ThisPass']:
			self.Errors['StartTime'] = GetTicks()

			if not self.Errors['Messages']:
				if not self.Errors['Title']:
					self.Errors['Title'] = self.GetText(f'Messages to {self.name}:', 'Title', pos=self.Errors['Pos'])

				self.Errors['Messages'] = [self.Errors['Title']]
				y = self.Errors['Pos'][1] + self.fonts['Title'].linesize

			else:
				y = self.Errors['Messages'][-1][1].y + self.fonts['Normal'].linesize

			x = self.Errors['Pos'][0]

			for Error in self.Errors['ThisPass']:
				self.Errors['Messages'].append(self.GetText(Error, 'Normal', pos=(x, y)))
				y += self.fonts['Normal'].linesize

		if self.Errors['Messages'] and GetTicks() > self.Errors['StartTime'] + 5000:
			self.Errors['Messages'].clear()

		while len(self.Errors['Messages']) > 5:
			self.Errors['Messages'].pop()

	def AttributeWait(self, Attribute):
		"""
		Three methods follow below that work together...
		...to allow the client-side script to 'do nothing' for a set period of time.
		"""

		with self.GameUpdatesNeeded:
			while self.Triggers['Server'].Events[Attribute] == self.Triggers['Client'].Events[Attribute]:
				pass

			self.Triggers['Client'].Events[Attribute] = self.Triggers['Server'].Events[Attribute]

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
			arg1.blit(*self.Surfaces[arg2].surfandpos)

		if CardFade and isinstance(arg1, SurfaceAndPosition):
			arg1.SetCoverRectOpacity(self.CoverRectOpacities[f'{arg1}'])
			self.BlitSurface(arg1, arg1.CoverRects)

		return arg1

	def TypeWriterText(self, text, WaitAfterwards=1200):
		"""Method for creating a 'typewriter effect' of text incrementally being blitted on the screen."""

		self.TypewriterEvents.put(text)

		while not self.TypewriterEvents.empty():
			pass

		for i, step in enumerate(text):
			self.TypewrittenText = i
			delay(30)

		if WaitAfterwards:
			delay(WaitAfterwards)

		self.TypewrittenText = -1

	def GetText(self, text, font='', colour=(0, 0, 0), pos=None, leftAlign=False, rightAlign=False):
		"""Function to generate rendered text and a pygame Rect object"""

		if pos:
			pos = (int(pos[0]), int(pos[1]))
		else:
			pos = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Surfaces['Game'].centre

		text = (self.fonts[font if font else 'Normal']).render(text, False, colour)

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
		self.Fill('Hand', 'Maroon')
		self.BlitSurface('Hand', self.player.Hand)

		if CardFade:
			self.BlitSurface('Hand', self.Surfaces['Hand'].CoverRects)

		self.Triggers['Client'].Surfaces['Hand'] = self.player.HandIteration

	def BuildBoardSurface(self, CardFade=False):
		self.Fill('Board', 'Maroon')

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
		self.Triggers['Client'].Surfaces['Board'] = self.Triggers['Server'].Surfaces['Board']

	def BuildTrumpCardSurface(self, CardFade=False):
		Trump = self.Attributes.TrumpCard
		self.Fill('TrumpCard', 'Maroon')
		Pos = (self.Surfaces['TrumpCard'].midpoint, (self.fonts['Normal'].linesize // 2))
		Text = self.GetText('Trumpcard', colour=self.CurrentColours['Text'], pos=Pos)
		self.BlitSurface('TrumpCard', [Text, Trump], CardFade=CardFade)
		self.Triggers['Client'].Surfaces['TrumpCard'] = self.Triggers['Server'].Surfaces['TrumpCard']

	def SurfaceUpdateRequired(self, name):
		return (
				self.Triggers['Server'].Surfaces[name] != self.Triggers['Client'].Surfaces[name]
				and name in self.SurfacesOnScreen
		)

	def UpdateSurfaces(self, BoardFade=False, ToUpdate=tuple(), CardFade=False):
		if self.Surfaces['BaseScoreboard'] and (self.SurfaceUpdateRequired('Scoreboard') or 'Scoreboard' in ToUpdate):
			try:
				self.BuildScoreboard('LightGrey')
			except:
				pass

		Condition = (self.player.HandIteration > self.Triggers['Client'].Surfaces['Hand']) or ('Hand' in ToUpdate)

		if (BoardFade or Condition) and 'Hand' in self.SurfacesOnScreen:
			try:
				self.BuildPlayerHand(CardFade=CardFade)
			except:
				pass

		if self.SurfaceUpdateRequired('Board') or BoardFade or 'Board' in ToUpdate:
			try:
				self.BuildBoardSurface(CardFade=CardFade)
			except:
				pass

		if self.SurfaceUpdateRequired('TrumpCard') or BoardFade or 'TrumpCard' in ToUpdate:
			try:
				self.BuildTrumpCardSurface(CardFade=CardFade)
			except:
				pass

	def UpdateGameSurface(self, Bidding=False, ToUpdate=tuple()):
		self.UpdateSurfaces(ToUpdate=ToUpdate)

		if Bidding:
			if self.player.Bid == -1:
				Message = self.GetText('Please enter your bid:', 'Title')
			elif not self.gameplayers.AllBid():
				try:
					Message = self.GetText(self.gameplayers.BidWaitingText(self.player.playerindex), 'Title')
				except:
					Message = False
			else:
				Message = False

			if Message:
				self.ToBlit.append(Message)

		if not Bidding and self.Errors['Messages']:
			self.ToBlit += self.Errors['Messages']

	def GetCursor(self, List, Pos):
		if time() % 1 > 0.5:
			List.append((self.Surfaces['Cursor'], Pos))
		return List

	def GetInputTextPos(self):
		BoardX, BoardY = self.Dimensions['BoardCentre']
		GameX, GameY = self.Surfaces['Game'].centre
		return (BoardX, (BoardY + 50)) if self.PlayStarted else (GameX, (GameY + 100))

	def BuildInputText(self):
		ToBlit = []

		if self.InputText:
			ToBlit.append((Message := self.GetText(self.InputText, pos=self.GetInputTextPos())))
			self.GetCursor(ToBlit, Message[1].topright)
		else:
			self.GetCursor(ToBlit, self.GetInputTextPos())

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
				self.BuildTrumpCardSurface(CardFade=True)
				self.BuildPlayerHand(CardFade=True)

		elif ScoreboardFade:
			self.BuildScoreboard(colour1)

		elif TextFade and FadeIn:
			self.BuildBoardSurface()
			self.BuildTrumpCardSurface(CardFade=True)

		for step in self.ColourTransition(colour1, colour2, OpacityTransition=CardFade, TimeToTake=TimeToTake):
			if ScoreboardFade:
				self.BuildScoreboard(step)
				self.CurrentColours['Scoreboard'] = step
			elif TextFade:
				self.CurrentColours['Text'] = step
				self.UpdateSurfaces(BoardFade=True, CardFade=True)
			elif CardFade:
				if FadeIn:
					ToUpdate = ('Hand', 'TrumpCard')
					self.CoverRectOpacities['Hand'] = self.CoverRectOpacities['TrumpCard'] = step
				elif EndOfTrickFade:
					ToUpdate = ('Board',)
					self.CoverRectOpacities['Board'] = step
				else:
					ToUpdate = ('TrumpCard',)
					self.CoverRectOpacities['TrumpCard'] = step

				self.UpdateSurfaces(CardFade=True, ToUpdate=ToUpdate)
			else:
				self.CurrentColours['Game'] = step
				if not FadeIn:
					self.BuildScoreboard(step)
					self.CurrentColours['Scoreboard'] = step

		self.UpdateSurfaces(ToUpdate=('Board', 'TrumpCard', 'Hand'))

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

	def NewScrollwheelVars(self):
		self.ScrollwheelDown = not self.ScrollwheelDown
		if self.ScrollwheelDown:
			self.ScrollwheelDownPos = pg.mouse.get_pos()
			self.ScrollwheelDownTime = self.OriginalScrollwheelDownTime = GetTicks()

	def ScrollwheelUp(self):
		self.ScrollwheelDown = False

	def MouseSetter(self):
		MousePos = pg.mouse.get_pos()
		Attrs = self.ClientSideAttributes
		Hand = self.player.Hand

		if self.ScrollwheelDown:
			DownX, DownY, MouseX, MouseY = *self.ScrollwheelDownPos, *MousePos
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
					self.CardHoverID = card.ID
					cur = 'Hand'

					if PlayedCards := self.Attributes.PlayedCards:
						SuitLed = PlayedCards[0].ActualSuit
						Condition = any(UnplayedCard.ActualSuit == SuitLed for UnplayedCard in Hand)

						if card.ActualSuit != SuitLed and Condition:
							cur = 'IllegalMove'
		else:
			cur = 'default'

		self.cur = cur
		pg.mouse.set_cursor(*self.Cursors[cur])
		
	def AddInputText(self, event):
		Input = self.InputText

		if event.unicode in PrintableCharactersPlusSpace:
			try:
				self.InputText += event.unicode
			finally:
				return None

		elif not Input:
			return None

		if (EvKey := event.key) == pg.K_BACKSPACE:
			self.InputText = Input[:-1]

		elif EvKey == pg.K_RETURN:
			if isinstance(self.name, int):
				if len(Input) < 30:
					# Don't need to check that letters are ASCII-compliant;
					# wouldn't have been able to type them if they weren't.
					self.name = Input
					self.ServerCommsQueue.put(('player', Input))
				else:
					self.Errors['ThisPass'].append('Name must be <30 characters; please try again.')

			elif not (self.Attributes.StartCardNumber or self.player.playerindex):
				# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
				try:
					assert 1 <= float(Input) <= self.MaxCardNumber and float(Input).is_integer()
					self.game.Attributes.StartCardNumber = int(Input)
					self.ServerCommsQueue.put(('CardNumber', Input))
				except:
					self.Errors['ThisPass'].append(f'Please enter an integer between 1 and {self.MaxCardNumber}')

			elif self.player.Bid == -1:
				# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
				Count = len(self.player.Hand)

				try:
					assert 0 <= float(Input) <= Count and float(Input).is_integer()
					self.game.PlayerMakesBid(Input, player=self.player)
					self.ServerCommsQueue.put(('Bid', Input))
				except:
					self.Errors['ThisPass'].append(f'Your bid must be an integer between 0 and {Count}.')

			self.InputText = ''
				
	def ExecutePlay(self):
		self.game.ExecutePlay(self.CardHoverID, self.player.playerindex)
		self.UpdateAttributesWithLock()
		self.ServerCommsQueue.put(('PlayCard', self.CardHoverID))


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

print('Initialising...')

try:
	# Try to calculate the size of the client's computer screen
	from screeninfo import get_monitors
	Monitor = get_monitors()[0]
	WindowDimensions = (WindowX, WindowY) = (Monitor.width, Monitor.height)
except:
	WindowDimensions = (WindowX, WindowY) = (1300, 680)

_, NewCardDimensions, RequiredResizeRatio = GetDimensions1(WindowDimensions)

CardIDs = [f'{p[0]}{p[1]}' for p in product(chain(range(2, 11), ('J', 'Q', 'K', 'A')), ('D', 'S', 'C', 'H'))]
CardImages = {CardID: Image.open(path.join('CardImages', f'{CardID}.jpg')).convert("RGB") for CardID in CardIDs}

CardImages = {
	key: value.resize((int(value.size[0] / RequiredResizeRatio), int(value.size[1] / RequiredResizeRatio)))
	for key, value in CardImages.items()
}

while True:
	try:
		with printing_exc():
			KnockTournament(WindowDimensions, NewCardDimensions, CardImages, IP, Port, password)
	except:
		print(f'Exception occurred at {GetTime()}')
		print(traceback.format_exc())
		pg.quit()

	if inputYesNo('Game has ended. Press enter to try to connect again and start a new game.', blank=True) == 'no':
		break
