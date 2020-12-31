#! Python3

"""This is the client-side script, that should be run by each player who wants to take part in the game."""


import sys, random, traceback

from FireworkParticle import Particle
from FireworkSparker import Sparker
from Network import *
from PasswordChecker import *
from ClientClasses import *
from Card import Card

from time import time
from PIL import Image
from os import chdir, environ, path
from itertools import chain, accumulate
from threading import Thread, Lock
from pyinputplus import inputCustom
from fractions import Fraction
from string import whitespace
from queue import Queue

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg


Display = pg.display
GetTicks = pg.time.get_ticks
delay = pg.time.delay
UpdateDisplay = Display.update
Rect = pg.Rect
Surface = pg.Surface
SysFont = pg.font.SysFont


# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
if getattr(sys, 'frozen', False):
	chdir(sys._MEIPASS)


class Window(object):
	"""

	Main object which contains the vast majority of the code for visualising the game on the client side.
	This object's methods also handle keyboard/mouse inputs, and various animations that happen throughout.

	"""

	__slots__ = 'GameUpdatesNeeded', 'lock', 'Triggers', 'fonts', 'gameplayers', 'Attributes', 'player', 'ToBlit', \
	            'InputText', 'Client', 'game', 'Window', 'CardImages', 'MessagesFromServer', 'Surfaces', 'PlayStarted', \
	            'ScoreboardAttributes', 'CoverRects',  'clock', 'PlayerTextPositions', 'name', 'Dimensions', 'Errors', \
	            'ServerCommsQueue', 'ClientSideAttributes', 'PlayerNumber', 'MaxCardNumber', 'StartCardPositions'

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

	def __init__(self, WindowDimensions, WindowMargin, CardDimensions, CardImages, IP, Port, password):
		self.lock = Lock()
		self.ServerCommsQueue = Queue()
		self.ScoreboardAttributes = {}
		self.InputText = ''
		self.GameUpdatesNeeded = False
		self.PlayStarted = False
		self.ToBlit = []		
		self.CoverRects = {'Hand': []}
		self.Attributes = AttributeTracker()

		self.ClientSideAttributes = {
			'GamesPlayed': 0,
			'CardNumberThisRound': -1,
			'RoundNumber': 1,
			'RoundLeaderIndex': -1,
			'TrickInProgress': False,
			'TrickNumber': 0,
			'WhoseTurnPlayerIndex': -1,
			'CardPositions': [],
			'PlayerOrder': []
		}

		WindowX, WindowY = WindowDimensions
		CardX, CardY = CardDimensions
		
		self.Dimensions = {
			'Window': WindowDimensions,
			'WindowMargin': WindowMargin,
			'Card': CardDimensions,
			'GameSurfaceCentre': ((WindowX // 2), (WindowY // 2))
		}
		
		self.Errors = {
			'Messages': [],
			'ThisPass': [],
			'Title': None,
			'Pos': (int(WindowX * Fraction(550, 683)), int(WindowY * Fraction(125, 192)))
		}

		self.Triggers = {
			'Client': Triggers(),
			'Server': Triggers()
		}

		pg.init()

		self.clock = pg.time.Clock()

		x = 10
		NormalFont = SysFont(self.DefaultFont, x, bold=True)
		UnderLineFont = SysFont(self.DefaultFont, x, bold=True)

		while x < 19:
			x += 1
			font = SysFont(self.DefaultFont, x, bold=True)
			font2 = SysFont(self.DefaultFont, x, bold=True)
			Size = font.size('Trick not in progress')

			if Size[0] > int(WindowX * Fraction(70, 683)) or Size[1] > int(WindowY * Fraction(18, 768)):
				break

			NormalFont = font
			UnderLineFont = font2

		x -= 1
		UnderLineFont.set_underline(True)

		self.fonts = {
			'Normal': FontAndLinesize(NormalFont),
			'UnderLine': FontAndLinesize(UnderLineFont),
			'Title': FontAndLinesize(SysFont(self.DefaultFont, 20, bold=True)),
			'Massive': FontAndLinesize(SysFont(self.DefaultFont, 40, bold=True))
		}

		BoardWidth = WindowX // 2
		BoardMid = BoardWidth // 2
		BoardPos = ((WindowX // 4), WindowMargin)
		BoardHeight = min(BoardWidth, (WindowY - BoardPos[1] - (CardDimensions[1] + 40)))
		BoardFifth = BoardHeight // 5

		self.Dimensions['BoardCentre'] = (BoardWidth, ((BoardHeight // 2) + WindowMargin))

		NormalLinesize = self.fonts['Normal'].linesize
		TripleLinesize = 3 * NormalLinesize
		TwoFifthsBoard, ThreeFifthsBoard = (BoardFifth * 2), (BoardFifth * 3)

		self.PlayerTextPositions = (
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

		CardRectsOnBoard = [Rect(*Tuple, *CardDimensions) for Tuple in (
			# Player1 - topleft
			((CardDimensions[0] + HalfCardWidth), (self.PlayerTextPositions[0][1] - HalfCardWidth)),

			# Player2 = topmid
			((BoardMid - HalfCardWidth), (self.PlayerTextPositions[1][1] + (NormalLinesize * 4))),

			# Player3 - topright
			((BoardWidth - (DoubleCardWidth + 60)), (self.PlayerTextPositions[2][1] - HalfCardWidth)),

			# Player4 = bottomright
			((BoardWidth - (DoubleCardWidth + 60)), (self.PlayerTextPositions[3][1] - HalfCardWidth)),

			# Player5 - bottommid
			((BoardMid - HalfCardWidth), (self.PlayerTextPositions[4][1] - CardDimensions[1] - NormalLinesize)),

			# Player6 - bottomleft
			(DoubleCardWidth, (self.PlayerTextPositions[5][1] - HalfCardWidth))

		)]

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

		Display.set_icon(pg.image.load(path.join('CardImages', 'PygameIcon.png')))
		self.Window = Display.set_mode(WindowDimensions, pg.FULLSCREEN)
		Display.set_caption('Knock (made by Alex Waygood)')

		self.CardImages = {
			ID: pg.image.fromstring(image.tobytes(), image.size, image.mode).convert()
			for ID, image in CardImages.items()
		}

		self.MessagesFromServer = {
			text: self.GetText(text, font='Massive')

			for text in (
				'Please enter your name:',
				'Waiting for all players to connect and enter their names.'
			)
		}

		Pos, font = self.Dimensions['BoardCentre'], 'Title'
		self.MessagesFromServer['Please enter your bid:'] = self.GetText('Please enter your bid:', font=font, pos=Pos)

		TrumpCardSurfaceDimensions = ((CardX + 2), (CardY + int(NormalLinesize * 2.5) + 10))
		TrumpCardPos = (Rect(1, int(NormalLinesize * 2.5), *CardDimensions),)

		self.Surfaces = {
			'BaseScoreboard': None,
			'Cursor': Surface((3, NormalLinesize)),

			'Scoreboard': SurfaceAndPosition(
				None,
				(WindowMargin, WindowMargin)
			),

			'Game': SurfaceAndPosition(
				Surface(WindowDimensions),
				(0, 0)
			),

			'TrumpCard': SurfaceAndPosition(
				Surface(TrumpCardSurfaceDimensions),
				((WindowX - (CardX + 50)), WindowMargin),
				TrumpCardPos,
				TrumpCardSurfaceDimensions
			),

			'Hand': SurfaceAndPosition(
				Surface((WindowX, (CardY + WindowMargin))),
				(0, (WindowY - (CardY + WindowMargin))),
				[]
			),

			'Board': SurfaceAndPosition(
				Surface((WindowX, WindowX)),
				BoardPos,
				CardRectsOnBoard
			),

			'blackSurf': SurfaceAndPosition(
				Surface(WindowDimensions).convert_alpha(),
				(0, 0)
			)

		}

		self.Fill('blackSurf', 'Black_fade')
		self.Fill('Cursor', 'Black')
		self.UpdateGameAttributes()

		Pos = TrumpCardPos[0]
		x, y = self.Surfaces['TrumpCard'].pos
		self.CoverRects['Trump'] = (Surface(CardDimensions), Rect((Pos.x + x), (Pos.y + y), *CardDimensions))

		print(f'Game display now initialising at {GetTime()}...')
		Thread(target=self.ThreadedGameUpdate).start()
		self.Errors['StartTime'] = GetTicks()

		# Menu sequence

		while isinstance(self.name, int):
			self.Fill(self.Window, 'LightGrey')
			self.ToBlit = [self.MessagesFromServer['Please enter your name:']]
			self.UpdateWindow(self.BlitInputText())

		while not self.ServerCommsQueue.empty():
			delay(1)

		delay(100)

		self.GameUpdatesNeeded = True

		while not self.gameplayers.AllPlayersJoinedGame():
			self.gameplayers = self.game.gameplayers
			self.CheckForExit()
			self.Fill(self.Window, 'LightGrey')

			if self.gameplayers.AllPlayersJoinedGame():
				break

			self.UpdateWindow([self.MessagesFromServer['Waiting for all players to connect and enter their names.']])

		while True:
			self.PlayGame(self.ClientSideAttributes['GamesPlayed'])
			self.ClientSideAttributes['GamesPlayed'] += 1

	def PlayGame(self, GamesPlayed):
		self.GameInitialisation(GamesPlayed)
		self.Wait(Attribute='StartNumberSet', FunctionOfGame=True, OutsideRound=True)

		for roundnumber, cardnumber, RoundLeader in zip(*self.game.GetGameParameters()):
			self.StartRound(roundnumber, cardnumber, RoundLeader, GamesPlayed)
			FirstPlayerIndex = RoundLeader.playerindex

			for i in range(cardnumber):
				FirstPlayerIndex = self.PlayTrick(FirstPlayerIndex, (i + 1), cardnumber)

			self.EndRound(FinalRound=(cardnumber == 1))

		self.EndGame(GamesPlayed)

	def GameInitialisation(self, GamesPlayed):
		self.GameUpdatesNeeded = False
		BoardColour = 'Maroon' if GamesPlayed else 'LightGrey'

		self.Fill('Game', BoardColour)

		if GamesPlayed:

			self.TypeWriterText(
				'NEW GAME STARTING:',
				WaitAfterwards=1000,
				WipeClean=True,
				PreGame=True,
				BoardColour=BoardColour
			)

		if self.player.playerindex and GamesPlayed:
			text = f"Waiting for {self.gameplayers[0]} to decide how many cards the game will start with."

		elif self.player.playerindex:
			text = f"As the first player to join this game, it is {self.gameplayers[0]}'s " \
			       f"turn to decide how many cards the game will start with."

		elif GamesPlayed:

			self.TypeWriterText(
				'Your turn to decide the starting card number!',
				WipeClean=True,
				PreGame=True,
				BoardColour=BoardColour
			)

			text = "Please enter how many cards you wish the game to start with:"

		else:
			text = "As the first player to join this game, it is your turn to decide " \
			       "how many cards you wish the game to start with:"

		self.TypeWriterText(text)
		self.GameUpdatesNeeded = True

		while not self.Attributes.StartCardNumber:
			self.ToBlit = [self.Surfaces['Game'].surfandpos]
			self.UpdateWindow(self.BlitInputText(CardNumberInput=True))

		self.GameUpdatesNeeded = False

		# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
		self.CalculateHandRectDimensions()

		self.Fill('Game', BoardColour)
		self.TypeWriterText('Click to start the game for all players!', WaitAfterwards=0)

		self.Wait(
			function=lambda x, y: not x.StartPlay,
			FunctionOfGame=True,
			ClicksNeeded=True,
			OutsideRound=True,
			ClickToStart=True
		)

		if not GamesPlayed:
			self.Fade('LightGrey', 'Maroon', TextFade=False, BoardColour=True)

		self.Fade('Maroon', 'LightGrey', TextFade=False, ScoreboardFade=True)

		self.Fill('Game', 'Maroon')
		self.BlitSurface('Game', 'Scoreboard')
		self.ServerCommsQueue.put('AC')
		self.PlayStarted = True

	def StartRound(self, RoundNumber, cardnumber, RoundLeader, GamesPlayed):
		self.GameUpdatesNeeded = False

		self.ClientSideAttributes.update({
			'CardNumberThisRound': cardnumber,
			'RoundLeaderIndex': RoundLeader.playerindex
		})

		Messages = (
			f'ROUND {RoundNumber} starting! This round has {cardnumber} card{"s" if cardnumber != 1 else ""}.',
			f'{RoundLeader.name} starts this round.'
		)

		for Message in Messages:
			self.TypeWriterText(Message, MidRound=False, UpdateGameSurfaceAfter=True)

		if not GamesPlayed and RoundNumber == 1:

			self.TypeWriterText(
				"Over the course of the game, your name will be underlined if it's your turn to play.",
				MidRound=False,
				WipeClean=True
			)

			self.TypeWriterText(
				'Press the Tab key at any time to toggle in and out of full-screen mode.',
				MidRound=False,
				UpdateGameSurfaceAfter=True
			)

		# Wait for the server to make a new pack of cards.
		self.Wait(Attribute='NewPack', FunctionOfGame=True, OutsideRound=True)

		self.TypeWriterText(
			f'The trumpcard for this round is the {self.Attributes.TrumpCard}, '
			f'which has been removed from the pack.',
			MidRound=False,
			UpdateGameSurfaceAfter=True
		)
		# change

		# Wait for the server to deal cards for this round.
		self.Wait(Attribute='CardsDealt', FunctionOfGame=True, OutsideRound=True)

		# Fade in the *player text on the board only*, then the cards in your hand + the trumpcard.
		CoverRects = self.Fade('Maroon', (0, 0, 0), FadeIn=True, UpdateGameSurfaceAfter=True)
		self.Fade(255, 0, List=CoverRects, TextFade=False, CardFade=True)
		self.Wait(TimeToWait=250, SwitchUpdatesOnBefore=False)

		for RectTuple in CoverRects:
			RectTuple[0].set_alpha(255)

		if RoundNumber == 1 and not GamesPlayed:
			self.TypeWriterText('Cards for this round have been dealt; each player must decide what they will bid.')

		# We need to enter our bid.
		self.Wait(
			FunctionOfGame=True,
			TypingNeeded=True,
			function=lambda x, y: x.gameplayers[self.player.playerindex].Bid == -1,
			Bidding=True,
			SwitchUpdatesOffAfter=False
		)

		while not self.ServerCommsQueue.empty():
			delay(1)

		delay(50)
		self.UpdateGameAttributes()

		# We now need to wait until everybody else has bid.
		if not self.gameplayers.AllBid():

			self.Wait(
				FunctionOfGame=True,
				function=lambda x, y: not x.gameplayers.AllBid(),
				Bidding=True,
				SwitchUpdatesOffAfter=False
			)

		self.Wait(TimeToWait=100)
		self.GameUpdatesNeeded = False

		# (Refresh the board.)
		self.GetGame(UpdateAfter=True)

		for Message in self.gameplayers.BidText(RoundLeader.playerindex):
			self.TypeWriterText(Message, WipeClean=True)

		self.ServerCommsQueue.put('AC')

	def PlayTrick(self, FirstPlayerIndex, TrickNumber, CardNumberThisRound):
		self.GameUpdatesNeeded = False

		self.ClientSideAttributes.update({
			'TrickInProgress': True,
			'TrickNumber': TrickNumber,
		})

		List1, List2 = self.StartCardPositions[FirstPlayerIndex:],  self.StartCardPositions[:FirstPlayerIndex]
		self.ClientSideAttributes['CardPositions'] = List1 + List2

		PlayerNo = self.PlayerNumber

		PlayerOrder = list(chain(range(FirstPlayerIndex, PlayerNo), range(FirstPlayerIndex)))
		self.ClientSideAttributes['PlayerOrder'] = PlayerOrder

		Pos = PlayerOrder.index(self.player.playerindex)
		self.ServerCommsQueue.put('AC')
		self.UpdateGameSurface(UpdateWindow=True)
		Text = f'{f"TRICK {TrickNumber} starting" if CardNumberThisRound != 1 else "TRICK STARTING"} :'
		self.TypeWriterText(Text, WipeClean=True)

		# Make sure the server is ready for the trick to start.
		self.Wait(Attribute='TrickStart', FunctionOfGame=True)

		# Tell the server we're ready to play the trick.
		self.BlockingMessageToServer('AC')
		self.GetGame(UpdateAfter=True)
		self.GameUpdatesNeeded = True

		# Play the trick, wait for all players to play.
		for i in range(PlayerNo):
			self.ClientSideAttributes['WhoseTurnPlayerIndex'] = PlayerOrder[i]
			while (CardsOnBoard := len(self.Attributes.PlayedCards)) == i:
				if CardsOnBoard != Pos:
					self.CheckForExit()
				else:
					self.HandleAllEvents(ClicksNeeded=True, TypingNeeded=False)
				self.UpdateGameSurface(UpdateWindow=True, ToUpdate=('Board',))

		self.GameUpdatesNeeded = False
		PlayedCards, trumpsuit = self.Attributes.PlayedCards, self.Attributes.trumpsuit
		PlayedCards = [card.DetermineWinValue(PlayedCards[0].ActualSuit, trumpsuit) for card in PlayedCards]

		(Winner := self.gameplayers[(max((card for card in PlayedCards), key=Card.GetWinValue)).PlayedBy]).WinsTrick()

		if TrickNumber != CardNumberThisRound:
			self.ClientSideAttributes.update({
				'WhoseTurnPlayerIndex': -1,
				'TrickInProgress': False
			})

			self.UpdateGameAttributes()

		self.Wait(TimeToWait=500, SwitchUpdatesOnBefore=False)
		Text = f'{Winner} won {f"trick {TrickNumber}" if CardNumberThisRound != 1 else "the trick"}!'
		self.TypeWriterText(Text, WipeClean=True)
		self.Attributes.PlayedCards.clear()
		self.UpdateGameSurface(UpdateWindow=True, ToUpdate=('Board',))

		if TrickNumber != CardNumberThisRound:
			self.ServerCommsQueue.put('AC')

		return Winner.playerindex

	def EndRound(self, FinalRound):
		self.GameUpdatesNeeded = False
		self.BuildScoreboard('LightGrey')
		self.BlitSurface('Game', 'Scoreboard')

		self.CoverRects['Trump'][0].set_alpha(0)
		self.Fade(0, 255, List=(self.CoverRects['Trump'],), FadeIn=False, TextFade=False, CardFade=True)
		self.Fade((0, 0, 0), 'Maroon', FadeIn=False)

		self.Fill('Game', 'Maroon')
		self.BlitSurface('Game', 'Scoreboard')

		self.ClientSideAttributes.update({
			'WhoseTurnPlayerIndex': -1,
			'TrickInProgress': False
		})

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

		self.Wait(SwitchUpdatesOnBefore=False, TimeToWait=500)

		for message in self.gameplayers.EndRoundText(FinalRound):
			self.TypeWriterText(message, WipeClean=True, MidRound=False)

		self.ServerCommsQueue.put('AC')

	def EndGame(self, GamesPlayed):
		self.GameUpdatesNeeded = False

		for text in self.gameplayers.GameCleanUp():
			self.TypeWriterText(text, MidRound=False, WipeClean=True)

		self.PlayStarted = False
		self.Wait(TimeToWait=500)
		self.Fade('LightGrey', 'Maroon', TextFade=False, ScoreboardFade=True)
		self.FireworksDisplay()
		self.Wait(TimeToWait=1000, UpdateWindow=False, OutsideRound=True)
		self.Fill('Game', 'Maroon')

		if GamesPlayed:
			for text in self.gameplayers.TournamentLeaders():
				self.TypeWriterText(text, PreGame=True, MidRound=False, WipeClean=True)

		self.TypeWriterText(
			'Press the spacebar to play again with the same players, or close the window to exit the game.',
			MidRound=False)

		self.Wait(Attribute='NewGameReset', FunctionOfGame=True, OutsideRound=True, GameReset=True)
		self.game.NewGameReset()
		self.player.ResetPlayer(self.PlayerNumber)
		self.Surfaces['BaseScoreboard'] = None
		self.ServerCommsQueue.put('AC')
		self.Surfaces['Hand'].RectList.clear()
		self.CoverRects['Hand'].clear()

	def ThreadedGameUpdate(self):
		"""This method runs throughout gameplay on a separate thread."""

		while True:
			while not self.ServerCommsQueue.empty():
				if isinstance((message := self.ServerCommsQueue.get()), str):
					self.GetGame(message, CheckForExit=False)
				else:
					self.SendToServer(*message)
			if self.GameUpdatesNeeded:
				self.GetGame(CheckForExit=False)

	def BlockingMessageToServer(self, message):
		(Q := self.ServerCommsQueue).put('AC')

		while not Q.empty():
			delay(1)

	def Fill(self, SurfaceObject, colour):
		if isinstance(SurfaceObject, str):
			SurfaceObject = self.Surfaces[SurfaceObject]

		SurfaceObject.fill(self.Colours[colour])
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
			CardList = [card.UpdateOnArrival(i, ListName, PlayerOrder, Surfaces) for i, card in enumerate(CardList)]

		self.player.ServerUpdate(self.GetPlayer())
		self.gameplayers.UpdateFromServer(self.game.gameplayers)
		self.Attributes = self.game.Attributes
		self.Triggers['Server'] = self.game.Triggers

	def GetGame(self, arg='GetGame', CheckForExit=True, UpdateAfter=False):
		with self.lock:
			self.game = self.Client.ClientSimpleSend(arg)

		self.UpdateGameAttributes()

		if CheckForExit:
			self.CheckForExit()

		if UpdateAfter:
			self.UpdateGameSurface(UpdateWindow=True)

	def SendToServer(self, MessageType, Message):
		with self.lock:
			self.game = self.Client.send(MessageType, Message)

		self.UpdateGameAttributes()

	def UpdateWindow(self, List=None):
		if List:
			self.Window.blits(List)
		else:
			self.BlitSurface(self.Window, 'Game')

		UpdateDisplay()

	def QuitGame(self):
		pg.quit()
		self.Client.CloseDown()
		raise Exception('The game has ended.')

	def HandleAllEvents(self, ClicksNeeded, TypingNeeded, ClickToStart=False, GameReset=False):
		"""

		Main 'event loop'

		"""

		self.Errors['ThisPass'].clear()
		click, SendInputText = False, False
		PlayerNo = self.PlayerNumber
		BidNeeded = (self.player.Bid == -1)

		for event in pg.event.get():
			if (EventType := event.type) == pg.QUIT or (len(self.gameplayers) != PlayerNo and self.game.StartPlay):
				self.QuitGame()

			elif EventType == pg.KEYDOWN and event.key == pg.K_TAB:
				Flags = 0 if pg.FULLSCREEN and self.Window.get_flags() else pg.FULLSCREEN
				self.Window = Display.set_mode(self.Dimensions['Window'], flags=Flags)

			elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE and self.Window.get_flags() and pg.FULLSCREEN:
				self.Window = Display.set_mode(self.Dimensions['Window'])

			if ClicksNeeded:
				if EventType == pg.MOUSEBUTTONDOWN:
					click = True
					MousePos = pg.mouse.get_pos()
				elif EventType == pg.MOUSEBUTTONUP:
					click = False

			elif EventType == pg.KEYDOWN:
				EventKey = event.key

				if GameReset and EventKey in (pg.K_SPACE, pg.K_RETURN):
					self.game.RepeatGame = True
					self.ServerCommsQueue.put('1')
				elif TypingNeeded:
					if event.unicode in PrintableCharacters:
						try:
							self.InputText += event.unicode
						except:
							pass
					elif self.InputText:
						if EventKey == pg.K_RETURN:
							SendInputText = True
						elif EventKey == pg.K_BACKSPACE:
							self.InputText = self.InputText[:-1]

		if click:
			if ClickToStart:
				self.game.StartPlay = True
				self.ServerCommsQueue.put('StartGame')

			else:
				for card in self.player.Hand:
					Result = card.Click(self.Attributes.PlayedCards, self.player.Hand, MousePos)
					if not Result:
						self.game.ExecutePlay(card.ID, self.player.playerindex)
						self.UpdateGameAttributes()
						self.ServerCommsQueue.put(('PlayCard', card.ID))
						delay(100)
					elif Result == 'Not clicked':
						pass
					else:
						self.Errors['ThisPass'].append(Result)

		if SendInputText:
			if isinstance(self.name, int):
				try:
					assert len(self.InputText) < 30
					assert all(any((letter in PrintableCharacters, letter in whitespace)) for letter in self.InputText)
					self.name = self.InputText
					self.ServerCommsQueue.put(('player', self.InputText))
				except:
					Errs = self.Errors['ThisPass']
					Errs.append('Name must be <30 characters, and ASCII-compliant; please try again.')

			elif not (self.Attributes.StartCardNumber or self.player.playerindex):
				Max = self.MaxCardNumber
				try:
					assert 1 <= float(self.InputText) <= Max
					assert float(self.InputText).is_integer()
					self.game.Attributes.StartCardNumber = int(self.InputText)
					self.ServerCommsQueue.put(('CardNumber', self.InputText))
				except:					
					self.Errors['ThisPass'].append(f'Please enter an integer between 1 and {Max}')

			elif BidNeeded:
				Count = len(self.player.Hand)
				try:
					assert 0 <= float(self.InputText) <= Count
					assert float(self.InputText).is_integer()
					self.game.PlayerMakesBid(self.InputText, player=self.player)
					self.ServerCommsQueue.put(('Bid', self.InputText))
				except:
					self.Errors['ThisPass'].append(f'Your bid must be an integer between 0 and {Count}.')

			self.InputText = ''

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

	def WaitFunction(self, x, y, Attribute, FunctionOfGame):
		"""
		Three methods follow below that work together...
		...to allow the client-side script to 'do nothing' for a set period of time.
		"""

		if FunctionOfGame:
			return self.Triggers['Server'].Events[Attribute] == self.Triggers['Client'].Events[Attribute]
		else:
			return x < y

	def WaitHelperFunction(self, FunctionOfGame, ClicksNeeded, TypingNeeded,
	                       Bidding, UpdateWindow, OutsideRound, ClickToStart, GameReset):

		Args = (ClicksNeeded, TypingNeeded, ClickToStart, GameReset)

		if any((FunctionOfGame, TypingNeeded, GameReset)):
			if OutsideRound:
				self.HandleAllEvents(*Args)
				self.UpdateWindow()
				return None
			self.UpdateGameSurface(Bidding=Bidding, UpdateWindow=False)

		self.HandleAllEvents(*Args)

		if UpdateWindow:
			self.UpdateWindow()

	def Wait(self, function=None, y=None, TimeToWait=0,  FunctionOfGame=False, ClicksNeeded=False,
	         TypingNeeded=False, Attribute='', Bidding=False, SwitchUpdatesOnBefore=True,
	         SwitchUpdatesOffAfter=True, UpdateWindow=True, OutsideRound=False, ClickToStart=False, GameReset=False):

		assert any((function, (FunctionOfGame and Attribute), (TimeToWait and not FunctionOfGame))), 'Incorrect arguments entered.'

		if SwitchUpdatesOnBefore:
			self.GameUpdatesNeeded = True

		y = 0 if FunctionOfGame else (GetTicks() + TimeToWait if not y else y)

		Args = (
			FunctionOfGame,
			ClicksNeeded,
			TypingNeeded,
			Bidding,
			UpdateWindow,
			OutsideRound,
			ClickToStart,
			GameReset
		)

		if function and not FunctionOfGame:
			while function(GetTicks(), y):
				self.WaitHelperFunction(*Args)

		elif function:
			while function(self.game, self):
				self.WaitHelperFunction(*Args)

		elif FunctionOfGame:
			while self.WaitFunction(0, y, Attribute, FunctionOfGame):
				self.WaitHelperFunction(*Args)

		else:
			while self.WaitFunction(GetTicks(), y, Attribute, FunctionOfGame):
				self.WaitHelperFunction(*Args)

		if SwitchUpdatesOffAfter:
			self.GameUpdatesNeeded = False

		if Attribute:
			self.Triggers['Client'].Events[Attribute] = self.Triggers['Server'].Events[Attribute]

	def BlitSurface(self, Surface1, Surface2):
		"""Method for simplifying the blitting of one surface to another."""

		if isinstance(Surface1, str):
			Surface1 = self.Surfaces[Surface1]

		if isinstance(Surface2, list):
			for Surface in Surface2:
				self.BlitSurface(Surface1, Surface)
		elif Surface2 in self.Surfaces:
			Surface1.blit(*self.Surfaces[Surface2].surfandpos)
		else:
			Surface1.blit(self.CardImages[Surface2.ID], Surface2.rect)

		return Surface1
	
	def TypeWriterText(self, text, WaitAfterwards=1200, WipeClean=False,
	                   MidRound=True, PreGame=False, BoardColour='Maroon',
	                   UpdateGameSurfaceAfter=False, TalkToServerDuring=False):

		"""Method for creating a 'typewriter effect' of text incrementally being blitted on the screen."""

		rect = Rect((0, 0), self.fonts['Title'].size(text))
		rect.center = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Dimensions['GameSurfaceCentre']
		TopLeft = rect.topleft

		RenderedSteps = [self.fonts['Title'].render(step, False, (0, 0, 0)) for step in accumulate(text)]

		for step in RenderedSteps:
			self.Surfaces['Game'].blit(step, TopLeft)
			if step != RenderedSteps[-1]:
				self.Wait(TimeToWait=30, SwitchUpdatesOnBefore=TalkToServerDuring)

		if WaitAfterwards:
			self.Wait(TimeToWait=WaitAfterwards, SwitchUpdatesOnBefore=TalkToServerDuring)

		if WipeClean:
			if MidRound and not PreGame:
				self.UpdateGameSurface(UpdateWindow=True)
			else:
				self.Fill('Game', BoardColour)
				if not PreGame:
					self.BlitSurface('Game', 'Scoreboard')
			self.Wait(TimeToWait=300, SwitchUpdatesOnBefore=TalkToServerDuring)

		if UpdateGameSurfaceAfter and not MidRound:
			self.UpdateGameSurface(RoundOpening=True)

	def CheckForExit(self):
		"""Shorter event loop for when no mouse/keyboard input is needed"""

		PlayerNo = self.PlayerNumber

		for event in pg.event.get():
			if event.type == pg.QUIT or (len(self.gameplayers) != PlayerNo and self.game.StartPlay):
				self.QuitGame()

			elif event.type == pg.KEYDOWN and event.key == pg.K_TAB:
				Flags = 0 if pg.FULLSCREEN and self.Window.get_flags() else pg.FULLSCREEN
				self.Window = Display.set_mode(self.Dimensions['Window'], flags=Flags)

			elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE and self.Window.get_flags() and pg.FULLSCREEN:
				self.Window = Display.set_mode(self.Dimensions['Window'])

		UpdateDisplay()

	def GetText(self, text, font='', colour=(0, 0, 0), pos=None, leftAlign=False, rightAlign=False):
		"""Function to generate rendered text and a pygame Rect object"""

		if pos:
			pos = (int(pos[0]), int(pos[1]))
		else:
			pos = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Dimensions['GameSurfaceCentre']

		text = (self.fonts[font if font else 'Normal']).render(text, False, colour)

		if leftAlign:
			rect = text.get_rect(topleft=pos)
		else:
			rect = text.get_rect(topright=pos) if rightAlign else text.get_rect(center=pos)

		return text, rect

	def SetScoreboardAttribute(self, Attribute, Value):
		"""Helper function for the scoreboard-building functions below"""

		self.ScoreboardAttributes[Attribute] = self.ScoreboardAttributes.get(Attribute, Value)
		return self.ScoreboardAttributes[Attribute]

	def BuildBaseScoreBoard(self):
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
		self.Surfaces['BaseScoreboard'] = Surface((ScoreboardWidth, ScoreboardHeight))
		self.SetScoreboardAttribute('Centre', (ScoreboardWidth // 2))

		self.SetScoreboardAttribute(
			'Title',
			self.GetText('SCOREBOARD', font='UnderLine', pos=(self.ScoreboardAttributes['Centre'], TitlePos))
		)

	def BuildScoreboard(self, ScoreboardColour=None):
		if not self.Surfaces['BaseScoreboard']:
			self.BuildBaseScoreBoard()

		if not ScoreboardColour:
			ScoreboardColour = self.Colours['LightGrey']
		elif isinstance(ScoreboardColour, str):
			ScoreboardColour = self.Colours[ScoreboardColour]

		ScoreboardSurface = self.Surfaces['BaseScoreboard'].copy()
		ScoreboardSurface.fill(ScoreboardColour)
		ScoreboardBlits = [self.ScoreboardAttributes['Title']]
		NormalLineSize = self.fonts['Normal'].linesize

		y = self.ScoreboardAttributes['TitlePos'] + NormalLineSize
		LeftMargin = self.ScoreboardAttributes['LeftMargin']

		for Message in self.gameplayers.ScoreboardText():
			Pos2 = ((self.ScoreboardAttributes['Width'] - LeftMargin), y)

			ScoreboardBlits += [
				self.GetText(Message[0], pos=(LeftMargin, y), leftAlign=True),
				self.GetText(Message[1], pos=Pos2, rightAlign=True)
			]

			y += NormalLineSize

		y += NormalLineSize * 2
		TrickNo, CardNo = self.ClientSideAttributes["TrickNumber"], self.ClientSideAttributes["CardNumberThisRound"]
		RoundNo, StartCardNo = self.ClientSideAttributes['RoundNumber'], self.Attributes.StartCardNumber
		TrickText = f'Trick {TrickNo} of {CardNo}' if TrickNo else 'Trick not in progress'

		ScoreboardBlits += [
			self.GetText(f'Round {RoundNo} of {StartCardNo}', pos=(self.ScoreboardAttributes['Centre'], y)),
			self.GetText(TrickText, pos=(self.ScoreboardAttributes['Centre'], (y + NormalLineSize)))
			]

		if self.ClientSideAttributes['GamesPlayed']:
			y += NormalLineSize * 3
			ScoreboardBlits.append(self.GetText('-----', pos=(self.ScoreboardAttributes['Centre'], y)))
			y += NormalLineSize

			for Message in self.gameplayers.ScoreboardText2():
				Pos2 = ((self.ScoreboardAttributes['Width'] - LeftMargin), y)

				ScoreboardBlits += [
					self.GetText(Message[0], pos=(LeftMargin, y), leftAlign=True),
					self.GetText(Message[1], pos=Pos2, rightAlign=True)
				]

				y += NormalLineSize

		ScoreboardSurface.blits(ScoreboardBlits)
		self.Surfaces['Scoreboard'].AddSurf(ScoreboardSurface)

	def BuildPlayerHand(self):
		self.Fill('Hand', 'Maroon')
		self.BlitSurface('Hand', self.player.Hand)
		self.Triggers['Client'].Surfaces['Hand'] = self.player.HandIteration

	def BuildBoardSurface(self, TextColour):
		self.Fill('Board', 'Maroon')
		BoardSurfaceBlits = [(self.CardImages[card.ID], card.rect) for card in self.Attributes.PlayedCards]

		Gen = self.gameplayers.BoardSurfaceText(
			self.PlayerTextPositions,
			self.fonts['Normal'].linesize,
			self.ClientSideAttributes['WhoseTurnPlayerIndex'],
			self.ClientSideAttributes['TrickInProgress'],
			len(self.Attributes.PlayedCards),
			self.ClientSideAttributes['RoundLeaderIndex']
		)

		BoardSurfaceBlits += [self.GetText(Tuple[0], font=Tuple[1], colour=TextColour, pos=Tuple[2]) for Tuple in Gen]
		self.Surfaces['Board'].blits(BoardSurfaceBlits)
		self.Triggers['Client'].Surfaces['Board'] = self.Triggers['Server'].Surfaces['Board']

	def BuildTrumpCardSurface(self, BoardTextColour=(0, 0, 0)):
		TrumpCard = self.Attributes.TrumpCard
		self.Fill('TrumpCard', 'Maroon')
		Pos = (self.Surfaces['TrumpCard'].midpoint, (self.fonts['Normal'].linesize // 2))
		Trump = (self.CardImages[TrumpCard.ID], TrumpCard.rect)
		self.Surfaces['TrumpCard'].blits((self.GetText('Trumpcard', colour=BoardTextColour, pos=Pos), Trump))
		self.Triggers['Client'].Surfaces['TrumpCard'] = self.Triggers['Server'].Surfaces['TrumpCard']

	def SurfaceUpdateRequired(self, name):
		return self.Triggers['Server'].Surfaces[name] != self.Triggers['Client'].Surfaces[name]

	def RoundInProgressBlits(self, BoardTextColour=(0, 0, 0), BoardFade=False, ToUpdate=tuple()):
		self.ToBlit.clear()

		if self.SurfaceUpdateRequired('Scoreboard') or 'Scoreboard' in ToUpdate:
			self.BuildScoreboard('LightGrey')

		Condition = (self.player.HandIteration > self.Triggers['Client'].Surfaces['Hand']) or ('Hand' in ToUpdate)

		if BoardFade or (self.player.Hand and Condition):
			self.BuildPlayerHand()

		if self.SurfaceUpdateRequired('Board') or BoardFade or 'Board' in ToUpdate:
			self.BuildBoardSurface(BoardTextColour)

		if self.SurfaceUpdateRequired('TrumpCard') or BoardFade or 'TrumpCard' in ToUpdate:
			self.BuildTrumpCardSurface(BoardTextColour)

		self.ToBlit += [self.Surfaces[name].surfandpos for name in ('Board', 'TrumpCard', 'Scoreboard')]

		if self.player.Hand:
			self.ToBlit.append(self.Surfaces['Hand'].surfandpos)

		return self.ToBlit

	def UpdateGameSurface(self, RoundOpening=False, Bidding=False, UpdateWindow=False, ToUpdate=tuple()):
		self.Fill('Game', 'Maroon')

		if RoundOpening:
			self.CheckForExit()
			self.BlitSurface('Game', 'Scoreboard')
			self.UpdateWindow()
			return None

		Condition = any((
			any(self.SurfaceUpdateRequired(attribute) for attribute in self.Triggers['Client'].Surfaces),
			ToUpdate
		))

		if Condition:
			self.RoundInProgressBlits(ToUpdate=ToUpdate)

		self.Surfaces['Game'].blits(self.ToBlit)

		if Bidding:
			if self.player.Bid == -1:
				Message = self.MessagesFromServer['Please enter your bid:']
			else:
				try:
					Pos = self.Dimensions['BoardCentre']
					Message = self.GetText(self.gameplayers.BidWaitingText(self.player.playerindex), 'Title', pos=Pos)
				except:
					Message = False

			if Message:
				self.Surfaces['Game'].blits(([Message] + self.BlitInputText(Bidding=True)))

		if self.Errors['Messages']:
			self.Surfaces['Game'].blits(self.Errors['Messages'])

		if UpdateWindow:
			self.UpdateWindow()

	def GetCursor(self, List, Pos):
		if time() % 1 > 0.5:
			List.append((self.Surfaces['Cursor'], Pos))
		return List

	def GetInputTextPos(self):
		BoardX, BoardY = self.Dimensions['BoardCentre']
		GameX, GameY = self.Dimensions['GameSurfaceCentre']
		return (BoardX, (BoardY + 50)) if self.PlayStarted else (GameX, (GameY + 100))

	def BlitInputText(self, CardNumberInput=False, Bidding=False):
		TypingNeeded = not self.player.playerindex if CardNumberInput else (self.player.Bid < 0 if Bidding else True)
		ToBlit = []
		self.HandleAllEvents(ClicksNeeded=False, TypingNeeded=TypingNeeded)

		if TypingNeeded:
			if self.InputText:
				ToBlit.append((Message := self.GetText(self.InputText, pos=self.GetInputTextPos())))
				ToBlit = self.GetCursor(ToBlit, Message[1].topright)
			else:
				ToBlit = self.GetCursor(ToBlit, self.GetInputTextPos())

			ToBlit += self.Errors['Messages']

		if not Bidding:
			self.ToBlit += ToBlit
			return self.ToBlit

		return ToBlit

	def CalculateHandRectDimensions(self):
		x = self.Dimensions['WindowMargin']
		DoubleWindowMargin = x * 2
		StartNumber = self.Attributes.StartCardNumber
		CardX, CardY = CardDimensions = self.Dimensions['Card']
		PotentialBuffer = CardX // 2
		WindowWidth = self.Dimensions['Window'][0]

		if ((CardX * StartNumber) + DoubleWindowMargin + (PotentialBuffer * (StartNumber - 1))) < WindowWidth:
			CardBufferInHand = PotentialBuffer
		else:
			CardBufferInHand = min(x, ((WindowWidth - DoubleWindowMargin - (CardX * StartNumber)) // (StartNumber - 1)))

		for i in range(StartNumber):
			self.Surfaces['Hand'].RectList.append(Rect(x, 0, *CardDimensions))
			x += CardX + CardBufferInHand

		self.CoverRects['Hand'] += [
			(Surface(CardDimensions), Rect(rect.x, (rect.y + self.Surfaces['Hand'].pos[1]), *CardDimensions))
			for rect in self.Surfaces['Hand'].RectList
		]

		for item in chain(self.CoverRects['Hand'], (self.CoverRects['Trump'],)):
			self.Fill(item[0], 'Maroon')

	def ColourTransition(self, colour1, colour2, OpacityTransition=False):
		"""Generator function for transitioning between either two colours or two opacity values"""

		if isinstance(colour1, str):
			colour1 = self.Colours[colour1]

		if isinstance(colour2, str):
			colour2 = self.Colours[colour2]

		if OpacityTransition:
			colour1, colour2 = [colour1], [colour2]

		StartTime = PreviousTime = GetTicks()
		EndTime = StartTime + 1000
		CurrentColour = colour1
		Range = range(1) if OpacityTransition else range(3)

		while (CurrentTime := GetTicks()) < EndTime:
			self.CheckForExit()
			Elapsed = CurrentTime - PreviousTime
			ColourStep = [(((colour2[i] - colour1[i]) / 1000) * Elapsed) for i in Range]
			CurrentColour = [CurrentColour[i] + ColourStep[i] for i in Range]

			if any(CurrentColour[i] < 0 or CurrentColour[i] > 255 for i in Range):
				break

			PreviousTime = CurrentTime
			yield CurrentColour[0] if OpacityTransition else CurrentColour

		yield colour2[0] if OpacityTransition else colour2

	def Fade(self, colour1, colour2, List=None, FadeIn=True, TextFade=True,
	         CardFade=False, ScoreboardFade=False, BoardColour=False, UpdateGameSurfaceAfter=False):

		"""Function for fading cards, text or the board colour, either in or out"""

		if FadeIn and TextFade:
			ToBlit2 = self.CoverRects['Hand'][:len(self.player.Hand)]
			ToBlit2.append(self.CoverRects['Trump'])
		else:
			ToBlit2 = []

		for step in self.ColourTransition(colour1, colour2, CardFade):
			self.Window.fill(step if BoardColour else self.Colours['Maroon'])

			if ScoreboardFade:
				self.BuildScoreboard(step)
				self.BlitSurface(self.Window, 'Scoreboard')
			elif TextFade:
				self.Window.blits(self.RoundInProgressBlits(BoardTextColour=step, BoardFade=True))
				self.Window.blits(ToBlit2 if FadeIn else (self.CoverRects['Trump'],))
			elif CardFade:
				for item in List:
					item[0].set_alpha(step)

				self.Window.blits(self.ToBlit)
				self.Window.blits(List)

			UpdateDisplay()

		if UpdateGameSurfaceAfter:
			self.UpdateGameSurface(UpdateWindow=False)

		return ToBlit2

	def FireworksDisplay(self):
		# This part of the code adapted from code by Adam Binks
		# Fade to black
		self.Fade('Maroon', (0, 0, 0), TextFade=False, BoardColour=True)

		# every frame blit a low alpha black surf so that all effects fade out slowly
		Duration = self.FireworkSettings['SecondsDuration'] * 1000
		StartTime = LastFirework = GetTicks()
		EndTime = StartTime + Duration
		RandomAmount = random.randint(*self.FireworkSettings['Bounds'])
		x, y = self.Dimensions['Window']

		# FIREWORK LOOP (adapted from code by Adam Binks)
		while (Time := GetTicks()) < EndTime or Particle.allParticles:
			dt = self.clock.tick(self.FireworkSettings['FPS']) / 60.0
			self.BlitSurface(self.Window, 'blackSurf')
			self.CheckForExit()

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
				item.draw(self.Window)

			UpdateDisplay()

		self.Fade((0, 0, 0), 'Maroon', TextFade=False, BoardColour=True)


print('Welcome to Knock!')
IP = 'alexknockparty.mywire.org'
Port = 5555

# IP = inputCustom(IPValidation, 'Please enter the IP address or hostname of the server you want to connect to: ')
# Port = inputInt('Please enter which port you wish to connect to: ', min=5000, max=65535)

password = inputCustom(
	PasswordInput,
	'Please enter the password to connect to this game, if one has been set (press Enter if none has been set): ',
	blank=True
)

print('Initialising...')

# Calculate the size of the window on the client's screen.

try:
	from screeninfo import get_monitors
	Monitor = get_monitors()[0]
	WindowDimensions = (Monitor.width, Monitor.height)
except:
	WindowDimensions = (1300, 680)

# Calculate the required size of the card images, based on various ratios of surfaces that will appear on the screen.
# Lots of "magic numbers" here, based purely on the principle of "keep the proportions that look good on my laptop".

WindowMargin = int(WindowDimensions[0] * Fraction(15, 683))
OriginalCardDimensions = (691, 1056)
WindowY = WindowDimensions[1]
ImpliedCardHeight = min(((WindowY // Fraction(768, 150)) - WindowMargin), (WindowY // 5.5))
ImpliedCardWidth = ImpliedCardHeight * Fraction(*OriginalCardDimensions)
NewCardDimensions = (ImpliedCardWidth.__ceil__(), ImpliedCardHeight.__ceil__())
RequiredResizeRatio = OriginalCardDimensions[1] / ImpliedCardHeight

CardIDs = [f'{value}{suit}' for suit in ('C', 'S', 'H', 'D') for value in chain(range(2, 11), ('J', 'Q', 'K', 'A'))]

CardImages = {CardID: Image.open(path.join('CardImages', f'{CardID}.jpg')).convert("RGB") for CardID in CardIDs}

CardImages = {
	key: value.resize((int(value.size[0] / RequiredResizeRatio), int(value.size[1] / RequiredResizeRatio)))
	for key, value in CardImages.items()
}

while True:
	try:
		window = Window(WindowDimensions, WindowMargin, NewCardDimensions, CardImages, IP, Port, password)
	except:
		print(f'Exception occurred at {GetTime()}')
		print(traceback.format_exc())
		pg.quit()

	Condition = (
			inputYesNo('Game has ended. Would you like to try to connect again and start a new game? ', blank=True)
			in ('no', '')
	)

	if Condition:
		break
