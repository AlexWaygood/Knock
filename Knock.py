#! Python3

"""This is the client-side script, that should be run by each player who wants to take part in the game."""


import sys, random, traceback

from FireworkParticle import Particle
from FireworkSparker import Sparker
from Network import *
from PasswordChecker import *
from ClientClasses import *

from time import time
from PIL import Image
from os import chdir, environ, path
from itertools import chain, accumulate
from threading import Thread, Lock
from pyinputplus import inputCustom
from fractions import Fraction

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg


# This is only relevant if you are using pyinstaller to convert this script into a .exe file.
if getattr(sys, 'frozen', False):
	chdir(sys._MEIPASS)


class Window(object):
	"""

	Main object which contains the vast majority of the code for visualising the game on the client side.
	This object's methods also handle keyboard/mouse inputs, and various animations that happen throughout.

	"""

	__slots__ = 'GameUpdatesNeeded', 'lock', 'Triggers', 'OperationsDict', 'fonts', 'gameplayers', 'Attributes', \
	            'player', 'ToBlit', 'InputText', 'Client', 'game', 'Window', 'CardImages', 'MessagesFromServer', \
	            'Surfaces', 'ScoreboardAttributes', 'CoverRects',  'clock', 'PlayerTextPositions', 'name', 'Dimensions', \
	            'Errors', 'PlayStarted'

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
		self.ScoreboardAttributes = {}
		self.InputText = ''
		self.GameUpdatesNeeded = False
		self.PlayStarted = False
		self.gameplayers = []
		self.ToBlit = []		
		self.CoverRects = {'Hand': []}
		self.Attributes = AttributeTracker()

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

		self.OperationsDict = {
			'GameInitialisation': self.GameInitialisation,
			'RoundStart': self.StartRound,
			'TrickStart': self.PlayTrick,
			'RoundEnd': self.EndRound,
			'WinnersAnnounced': self.EndGame
		}

		self.Triggers = {
			'Client': Triggers(),
			'Server': Triggers()
		}

		pg.init()

		self.clock = pg.time.Clock()

		x = 10
		NormalFont = pg.font.SysFont(self.DefaultFont, x, bold=True)
		UnderLineFont = pg.font.SysFont(self.DefaultFont, x, bold=True)

		while x < 19:
			x += 1
			font = pg.font.SysFont(self.DefaultFont, x, bold=True)
			font2 = pg.font.SysFont(self.DefaultFont, x, bold=True)
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
			'Title': FontAndLinesize(pg.font.SysFont(self.DefaultFont, 20, bold=True)),
			'Massive': FontAndLinesize(pg.font.SysFont(self.DefaultFont, 40, bold=True))
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

		CardRectsOnBoard = [pg.Rect(*Tuple, *CardDimensions) for Tuple in (
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

			print('Connection failed; trying again.')

		print(f'Connected at {GetTime()}.')

		assert self.game, "Couldn't get a copy of the game. Have the maximum number of players already joined?"

		self.name = self.player.playerindex
		self.UpdateGameAttributes()

		pg.display.set_icon(pg.image.load(path.join('CardImages', 'PygameIcon.png')))
		self.Window = pg.display.set_mode(WindowDimensions, pg.FULLSCREEN)
		pg.display.set_caption('Knock (made by Alex Waygood)')

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

		self.MessagesFromServer['Please enter your bid:'] = self.GetText(
			'Please enter your bid:',
			font='Title',
			pos=self.Dimensions['BoardCentre']
		)

		TrumpCardSurfaceDimensions = ((CardX + 2), (CardY + int(NormalLinesize * 2.5) + 10))
		TrumpCardPos = (pg.Rect(1, int(NormalLinesize * 2.5), *CardDimensions),)

		self.Surfaces = {
			'BaseScoreboard': None,
			'Cursor': pg.Surface((3, NormalLinesize)),

			'Scoreboard': SurfaceAndPosition(
				None,
				(WindowMargin, WindowMargin)
			),

			'Game': SurfaceAndPosition(
				pg.Surface(WindowDimensions),
				(0, 0)
			),

			'TrumpCard': SurfaceAndPosition(
				pg.Surface(TrumpCardSurfaceDimensions),
				((WindowX - (CardX + 50)), WindowMargin),
				TrumpCardPos,
				TrumpCardSurfaceDimensions
			),

			'Hand': SurfaceAndPosition(
				pg.Surface((WindowX, (CardY + WindowMargin))),
				(0, (WindowY - (CardY + WindowMargin))),
				[]
			),

			'Board': SurfaceAndPosition(
				pg.Surface((WindowX, WindowX)),
				BoardPos,
				CardRectsOnBoard
			),

			'blackSurf': SurfaceAndPosition(
				pg.Surface(WindowDimensions).convert_alpha(),
				(0, 0)
			)

		}

		self.Fill('blackSurf', 'Black_fade')
		self.Fill('Cursor', 'Black')

		Pos = TrumpCardPos[0]
		x, y = self.Surfaces['TrumpCard'].pos
		self.CoverRects['Trump'] = (pg.Surface(CardDimensions), pg.Rect((Pos.x + x), (Pos.y + y), *CardDimensions))

		print(f'Game display now initialising at {GetTime()}...')

		thread = Thread(target=self.ThreadedGameUpdate)
		thread.start()
		
		self.Errors['StartTime'] = pg.time.get_ticks()

		# Menu sequence

		while isinstance(self.name, int):
			self.Fill(self.Window, 'LightGrey')
			self.ToBlit = [self.MessagesFromServer['Please enter your name:']]
			self.UpdateWindow(self.BlitInputText())

		self.GameUpdatesNeeded = True
		PlayerNo = self.Attributes.Tournament['PlayerNumber']

		while any(isinstance(player.name, int) for player in self.gameplayers) or len(self.gameplayers) < PlayerNo:
			self.CheckForExit()
			self.Fill(self.Window, 'LightGrey')
			self.UpdateWindow([self.MessagesFromServer['Waiting for all players to connect and enter their names.']])

		# Main gameplay loop

		while True:
			self.GameUpdatesNeeded = True

			for condition, function in self.OperationsDict.items():
				if self.Triggers['Server'].Events[condition] > self.Triggers['Client'].Events[condition]:
					self.GameUpdatesNeeded = False
					self.Triggers['Client'].Events[condition] = self.Triggers['Server'].Events[condition]
					function()
					self.GameUpdatesNeeded = True

	def ThreadedGameUpdate(self):
		"""This method runs throughout gameplay on a separate thread."""

		while True:
			if self.GameUpdatesNeeded:
				self.GetGame(CheckForExit=False)

	def Fill(self, SurfaceObject, colour):
		if isinstance(SurfaceObject, str):
			SurfaceObject = self.Surfaces[SurfaceObject]

		SurfaceObject.fill(self.Colours[colour])
		return SurfaceObject

	def Updaterects(self, List, Surface):
		"""Helper method for the below method"""

		for card in List:
			card.rect = self.Surfaces[Surface].RectList[card.PosIndex]
			card.colliderect = card.rect.move(*self.Surfaces[Surface].pos)

	def UpdateGameAttributes(self):
		"""

		Upon receiving an updated copy of the game from the server...
		...This method ensures an immediate update of the client-side copies of all the game's attributes

		"""

		self.gameplayers = self.game.Attributes.Tournament['gameplayers']
		self.player = next(player for player in self.gameplayers if player.name == self.name)

		self.Updaterects(self.player.Hand, 'Hand')
		self.Updaterects(self.game.Attributes.Trick['PlayedCards'], 'Board')

		if TrumpCard := self.game.Attributes.Round['TrumpCard']:
			self.Updaterects((TrumpCard,), 'TrumpCard')

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

		pg.display.update()

	def QuitGame(self):
		pg.quit()
		self.Client.CloseDown()
		raise Exception('The game has ended.')

	def HandleAllEvents(self, ClicksNeeded, TypingNeeded):
		"""Main 'event loop'"""

		self.Errors['ThisPass'].clear()
		click = False
		SendInputText = False
		PlayerNo = self.Attributes.Tournament['PlayerNumber']

		for event in pg.event.get():
			if event.type == pg.QUIT or (len(self.gameplayers) != PlayerNo and self.game.StartPlay):
				self.QuitGame()

			elif event.type == pg.KEYDOWN and event.key == pg.K_TAB:
				Flags = 0 if pg.FULLSCREEN and self.Window.get_flags() else pg.FULLSCREEN
				self.Window = pg.display.set_mode(self.Dimensions['Window'], flags=Flags)

			elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE and self.Window.get_flags() and pg.FULLSCREEN:
				self.Window = pg.display.set_mode(self.Dimensions['Window'])

			if ClicksNeeded:
				if event.type == pg.MOUSEBUTTONDOWN:
					click = True
				elif event.type == pg.MOUSEBUTTONUP:
					click = False

			elif TypingNeeded and event.type == pg.KEYDOWN:
				if not self.game.RepeatGame and event.key in (pg.K_SPACE, pg.K_RETURN):
					self.GetGame('1', CheckForExit=False)
					return None
				elif event.unicode in PrintableCharacters:
					try:
						self.InputText += event.unicode
					except:
						pass
				elif self.InputText:
					if event.key == pg.K_RETURN:
						SendInputText = True
					elif event.key == pg.K_BACKSPACE:
						self.InputText = self.InputText[:-1]

		if click:
			MousePos = pg.mouse.get_pos()
			Dict = self.Attributes.Trick

			if not self.game.StartPlay:
				self.GetGame('StartGame')

			elif Dict['TrickInProgress'] and Dict['WhoseTurnPlayerIndex'] == self.player.playerindex:
				for card in self.player.Hand:
					if (Result := card.Click(self.game, MousePos)) == 'Not clicked':
						pass
					elif Result:
						self.Errors['ThisPass'].append(Result)
					else:
						self.SendToServer('PlayCard', card.ID)

		if SendInputText:
			if isinstance(self.name, int):
				self.name = self.InputText
				self.SendToServer('player', self.InputText)

			elif not (self.Attributes.Game['StartCardNumber'] or self.player.playerindex):
				Max = self.Attributes.Tournament['MaxCardNumber']
				try:
					assert 1 <= float(self.InputText) <= Max
					assert float(self.InputText).is_integer()
					self.SendToServer('CardNumber', int(self.InputText))
				except:					
					self.Errors['ThisPass'].append(f'Please enter an integer between 1 and {Max}')

			elif self.player.Bid == -1:
				Count = len(self.player.Hand)
				try:
					assert 0 <= float(self.InputText) <= Count
					assert float(self.InputText).is_integer()
					self.SendToServer('Bid', self.InputText)
				except:
					self.Errors['ThisPass'].append(f'Your bid must be an integer between 0 and {Count}.')

			self.InputText = ''

		if self.Errors['ThisPass']:
			self.Errors['StartTime'] = pg.time.get_ticks()

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

		if self.Errors['Messages'] and pg.time.get_ticks() > self.Errors['StartTime'] + 5000:
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

	def WaitHelperFunction(self, FunctionOfGame, ClicksNeeded, TypingNeeded, Bidding, UpdateWindow, OutsideRound):
		if FunctionOfGame or TypingNeeded:
			if OutsideRound:
				self.HandleAllEvents(ClicksNeeded, TypingNeeded)
				self.UpdateWindow()
				return None
			self.UpdateGameSurface(Bidding=Bidding, UpdateWindow=False)

		self.HandleAllEvents(ClicksNeeded, TypingNeeded)

		if UpdateWindow:
			self.UpdateWindow()

	def Wait(self, function=None, y=None, TimeToWait=0,  FunctionOfGame=False, ClicksNeeded=False,
	         TypingNeeded=False, Attribute='', Bidding=False, SwitchUpdatesOnBefore=True,
	         SwitchUpdatesOffAfter=True, UpdateWindow=True, OutsideRound=False):

		assert function or (FunctionOfGame and Attribute) or (TimeToWait and not FunctionOfGame), 'Incorrect arguments entered.'

		if SwitchUpdatesOnBefore:
			self.GameUpdatesNeeded = True

		y = 0 if FunctionOfGame else (pg.time.get_ticks() + TimeToWait if not y else y)

		if function and not FunctionOfGame:
			while function(pg.time.get_ticks(), y):
				self.WaitHelperFunction(FunctionOfGame, ClicksNeeded, TypingNeeded, Bidding, UpdateWindow, OutsideRound)

		elif function:
			while function(self.game, self):
				self.WaitHelperFunction(FunctionOfGame, ClicksNeeded, TypingNeeded, Bidding, UpdateWindow, OutsideRound)

		elif FunctionOfGame:
			while self.WaitFunction(0, y, Attribute, FunctionOfGame):
				self.WaitHelperFunction(FunctionOfGame, ClicksNeeded, TypingNeeded, Bidding, UpdateWindow, OutsideRound)

		else:
			while self.WaitFunction(pg.time.get_ticks(), y, Attribute, FunctionOfGame):
				self.WaitHelperFunction(FunctionOfGame, ClicksNeeded, TypingNeeded, Bidding, UpdateWindow, OutsideRound)

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
	
	def TypeWriterText(self, text, WaitAfterwards=700, WipeClean=False,
	                   MidRound=True, PreGame=False, BoardColour='Maroon',
	                   UpdateGameSurfaceAfter=False):

		"""Method for creating a 'typewriter effect' of text incrementally being blitted on the screen."""

		rect = pg.Rect((0, 0), self.fonts['Title'].size(text))
		rect.center = self.Dimensions['BoardCentre'] if self.PlayStarted else self.Dimensions['GameSurfaceCentre']
		TopLeft = rect.topleft

		RenderedSteps = [self.fonts['Title'].render(step, False, (0, 0, 0)) for step in accumulate(text)]

		for step in RenderedSteps:
			self.Surfaces['Game'].blit(step, TopLeft)
			if step != RenderedSteps[-1]:
				self.Wait(TimeToWait=30)

		if WaitAfterwards:
			self.Wait(TimeToWait=WaitAfterwards)

		if WipeClean:
			if MidRound and not PreGame:
				self.UpdateGameSurface(UpdateWindow=True)
			else:
				self.Fill('Game', BoardColour)
				if not PreGame:
					self.BlitSurface('Game', 'Scoreboard')
			self.Wait(TimeToWait=300)

		if UpdateGameSurfaceAfter and not MidRound:
			self.UpdateGameSurface(RoundOpening=True)

	def CheckForExit(self):
		"""Shorter event loop for when no mouse/keyboard input is needed"""

		PlayerNo = self.Attributes.Tournament['PlayerNumber']

		for event in pg.event.get():
			if event.type == pg.QUIT or (len(self.gameplayers) != PlayerNo and self.game.StartPlay):
				self.QuitGame()

			elif event.type == pg.KEYDOWN and event.key == pg.K_TAB:
				Flags = 0 if pg.FULLSCREEN and self.Window.get_flags() else pg.FULLSCREEN
				self.Window = pg.display.set_mode(self.Dimensions['Window'], flags=Flags)

			elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE and self.Window.get_flags() and pg.FULLSCREEN:
				self.Window = pg.display.set_mode(self.Dimensions['Window'])

		pg.display.update()

	def GetText(self, text, font='', colour=(0, 0, 0), pos=None, leftAlign=False, rightAlign=False):
		"""Function to generate rendered text and a pg.Rect object"""

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

	def BuildBaseScoreBoard(self):
		NormalLineSize = self.fonts['Normal'].linesize
		LeftMargin = int(NormalLineSize * 1.75)
		TitlePos = int(NormalLineSize * 1.5)

		MaxPointsText = max(self.fonts['Normal'].size(f'{str(player)}: 88 points')[0] for player in self.gameplayers)

		ScoreboardWidth = self.ScoreboardAttributes['Width'] = self.ScoreboardAttributes.get(
			'Width',
			(2 * LeftMargin) + max(MaxPointsText, self.fonts['UnderLine'].size('Trick not in progress')[0])
		)

		Dict = self.Attributes.Tournament
		Multiplier = ((Dict['PlayerNumber'] * 2) + 7) if Dict['GamesPlayed'] else (Dict['PlayerNumber'] + 4)

		ScoreboardHeight = (NormalLineSize * Multiplier) + (2 * LeftMargin)
		self.Surfaces['BaseScoreboard'] = pg.Surface((ScoreboardWidth, ScoreboardHeight))
		self.ScoreboardAttributes['Centre'] = self.ScoreboardAttributes.get('Centre', (ScoreboardWidth // 2))

		self.ScoreboardAttributes['Title'] = self.ScoreboardAttributes.get(
			'Title',
			self.GetText('SCOREBOARD', font='UnderLine', pos=(self.ScoreboardAttributes['Centre'], TitlePos))
		)

		self.ScoreboardAttributes['LeftMargin'], self.ScoreboardAttributes['TitlePos'] = LeftMargin, TitlePos

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

		for player in sorted(self.gameplayers, key=Player.GetPoints, reverse=True):
			Pos2 = ((self.ScoreboardAttributes['Width'] - LeftMargin), y)

			ScoreboardBlits += [
				self.GetText(f'{player}:', pos=(LeftMargin, y), leftAlign=True),
				self.GetText(f'{player.Points} point{"s" if player.Points != 1 else ""}', pos=Pos2, rightAlign=True)
			]

			y += NormalLineSize

		y += NormalLineSize * 2
		TrickNo, CardNo = self.Attributes.Trick["TrickNumber"], self.Attributes.Round["CardNumberThisRound"]
		RoundNo, StartCardNo = self.Attributes.Round['RoundNumber'], self.Attributes.Game['StartCardNumber']
		TrickText = f'Trick {TrickNo} of {CardNo}' if TrickNo else 'Trick not in progress'

		ScoreboardBlits += [
			self.GetText(f'Round {RoundNo} of {StartCardNo}', pos=(self.ScoreboardAttributes['Centre'], y)),
			self.GetText(TrickText, pos=(self.ScoreboardAttributes['Centre'], (y + NormalLineSize)))
			]

		if self.Attributes.Tournament['GamesPlayed']:
			y += NormalLineSize * 3
			ScoreboardBlits.append(self.GetText('-----', pos=(self.ScoreboardAttributes['Centre'], y)))
			y += NormalLineSize

			for player in sorted(self.gameplayers, key=Player.GetGamesWon, reverse=True):
				Text2 = f'{player.GamesWon} game{"s" if player.GamesWon != 1 else ""}'
				Pos2 = ((self.ScoreboardAttributes['Width'] - LeftMargin), y)

				ScoreboardBlits += [
					self.GetText(f'{player}:', pos=(LeftMargin, y), leftAlign=True),
					self.GetText(Text2, pos=Pos2, rightAlign=True)
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
		LineSize = self.fonts['Normal'].linesize
		players = self.gameplayers

		BoardSurfaceBlits = [(self.CardImages[card.ID], card.rect) for card in self.Attributes.Trick['PlayedCards']]

		for player in players:
			BaseX, BaseY = Pos = self.PlayerTextPositions[player.playerindex]
			Bid = player.Bid
			BidText = 'unknown' if Bid < 0 else (Bid if all(player.Bid > -1 for player in players) else 'received')
			Pos3 = (BaseX, (BaseY + (LineSize * 2)))

			condition = (
					(Dict := self.Attributes.Trick)['WhoseTurnPlayerIndex'] == player.playerindex
					and Dict['TrickInProgress']
					and len(Dict['PlayedCards']) < self.Attributes.Tournament['PlayerNumber']
			)

			BoardSurfaceBlits += [
				self.GetText(player.name, font=('UnderLine' if condition else 'Normal'), colour=TextColour, pos=Pos),
				self.GetText(f'Bid {BidText}', colour=TextColour, pos=(BaseX, (BaseY + LineSize))),
				self.GetText(f'{player.Tricks} trick{"" if player.Tricks == 1 else "s"}', colour=TextColour, pos=Pos3)
			]

			if player.RoundLeader and any(player.Bid == -1 for player in self.gameplayers):
				Pos = (BaseX, (BaseY + (LineSize * 3)))
				BoardSurfaceBlits.append(self.GetText('Leads this round', colour=TextColour, pos=Pos))

		self.Surfaces['Board'].blits(BoardSurfaceBlits)
		self.Triggers['Client'].Surfaces['CurrentBoard'] = self.Triggers['Server'].Surfaces['CurrentBoard']

	def BuildTrumpCardSurface(self, BoardTextColour=(0, 0, 0)):
		TrumpCard = self.Attributes.Round['TrumpCard']
		self.Fill('TrumpCard', 'Maroon')
		Pos = (self.Surfaces['TrumpCard'].midpoint, (self.fonts['Normal'].linesize // 2))
		Trump = (self.CardImages[TrumpCard.ID], TrumpCard.rect)
		self.Surfaces['TrumpCard'].blits((self.GetText('Trumpcard', colour=BoardTextColour, pos=Pos), Trump))
		self.Triggers['Client'].Surfaces['TrumpCard'] = self.Triggers['Server'].Surfaces['TrumpCard']

	def SurfaceUpdateRequired(self, name):
		return self.Triggers['Server'].Surfaces[name] > self.Triggers['Client'].Surfaces[name]

	def RoundInProgressBlits(self, BoardTextColour=(0, 0, 0), BoardFade=False):
		self.ToBlit.clear()

		if self.SurfaceUpdateRequired('Scoreboard'):
			self.BuildScoreboard('LightGrey')

		if (self.player.Hand and self.player.HandIteration > self.Triggers['Client'].Surfaces['Hand']) or BoardFade:
			self.BuildPlayerHand()

		if self.SurfaceUpdateRequired('CurrentBoard') or BoardFade:
			self.BuildBoardSurface(BoardTextColour)

		if self.SurfaceUpdateRequired('TrumpCard') or BoardFade:
			self.BuildTrumpCardSurface(BoardTextColour)

		self.ToBlit += [self.Surfaces[name].surfandpos for name in ('Board', 'TrumpCard', 'Scoreboard')]

		if self.player.Hand:
			self.ToBlit.append(self.Surfaces['Hand'].surfandpos)

		return self.ToBlit

	def UpdateGameSurface(self, RoundOpening=False, Bidding=False, UpdateWindow=False):
		self.Fill('Game', 'Maroon')

		if RoundOpening:
			self.CheckForExit()
			self.BlitSurface('Game', 'Scoreboard')
			self.UpdateWindow()
			return None

		if any(self.SurfaceUpdateRequired(attribute) for attribute in self.Triggers['Client'].Surfaces):
			self.RoundInProgressBlits()

		self.Surfaces['Game'].blits(self.ToBlit)

		if Bidding:
			if self.player.Bid == -1:
				Message = self.MessagesFromServer['Please enter your bid:']
			else:
				try:
					if self.Attributes.Tournament['PlayerNumber'] != 2:
						if (PlayersNotBid := sum(1 for player in self.gameplayers if player.Bid == -1)) > 1:
							WaitingText = f'{PlayersNotBid} remaining players'
						else:
							WaitingText = next(player.name for player in self.gameplayers if player.Bid == -1)
					else:
						WaitingText = self.gameplayers[0 if self.player.playerindex else 1].name

					Pos = self.Dimensions['BoardCentre']
					Message = self.GetText(f'Waiting for {WaitingText} to bid.', 'Title', pos=Pos)

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
		StartNumber = self.Attributes.Game['StartCardNumber']
		CardX, CardY = CardDimensions = self.Dimensions['Card']
		PotentialBuffer = CardX // 2
		WindowWidth = self.Dimensions['Window'][0]

		if ((CardX * StartNumber) + DoubleWindowMargin + (PotentialBuffer * (StartNumber - 1))) < WindowWidth:
			CardBufferInHand = PotentialBuffer
		else:
			CardBufferInHand = min(x, ((WindowWidth - DoubleWindowMargin - (CardX * StartNumber)) // (StartNumber - 1)))

		for i in range(StartNumber):
			self.Surfaces['Hand'].RectList.append(pg.Rect(x, 0, *CardDimensions))
			x += CardX + CardBufferInHand

		self.CoverRects['Hand'] += [
			(pg.Surface(CardDimensions), pg.Rect(rect.x, (rect.y + self.Surfaces['Hand'].pos[1]), *CardDimensions))
			for rect in self.Surfaces['Hand'].RectList
		]

		for item in chain(self.CoverRects['Hand'], (self.CoverRects['Trump'],)):
			self.Fill(item[0], 'Maroon')

	def GameInitialisation(self):
		BoardColour = 'Maroon' if self.Attributes.Tournament['GamesPlayed'] else 'LightGrey'

		self.Fill('Game', BoardColour)
		if self.Attributes.Tournament['GamesPlayed']:

			self.TypeWriterText(
				'NEW GAME STARTING:',
				WaitAfterwards=1000,
				WipeClean=True,
				PreGame=True,
				BoardColour=BoardColour
			)

		if self.player.playerindex and self.Attributes.Tournament['GamesPlayed']:
			text = f"Waiting for {self.gameplayers[0]} to decide how many cards the game will start with."

		elif self.player.playerindex:
			text = f"As the first player to join this game, it is {self.gameplayers[0]}'s " \
			       f"turn to decide how many cards the game will start with."

		elif self.Attributes.Tournament['GamesPlayed']:

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

		while not self.Attributes.Game['StartCardNumber']:
			self.ToBlit = [self.Surfaces['Game'].surfandpos]
			self.UpdateWindow(self.BlitInputText(CardNumberInput=True))

		# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
		self.CalculateHandRectDimensions()

		self.Fill('Game', BoardColour)
		self.TypeWriterText('Click to start the game for all players!', WaitAfterwards=0)

		self.Wait(function=lambda x, y: not x.StartPlay, FunctionOfGame=True, ClicksNeeded=True, OutsideRound=True)

		if not self.Attributes.Tournament['GamesPlayed']:
			self.Fade('LightGrey', 'Maroon', TextFade=False, BoardColour=True)

		self.Fade('Maroon', 'LightGrey', TextFade=False, ScoreboardFade=True)

		self.Fill('Game', 'Maroon')
		self.BlitSurface('Game', 'Scoreboard')

		try:
			self.GetGame('AC')
		except:
			pass

		self.PlayStarted = True

	def ColourTransition(self, colour1, colour2, OpacityTransition=False):
		"""Generator function for transitioning between either two colours or two opacity values"""

		if isinstance(colour1, str):
			colour1 = self.Colours[colour1]

		if isinstance(colour2, str):
			colour2 = self.Colours[colour2]

		if OpacityTransition:
			colour1, colour2 = [colour1], [colour2]

		StartTime = PreviousTime = pg.time.get_ticks()
		EndTime = StartTime + 1000
		CurrentColour = colour1
		Range = range(1) if OpacityTransition else range(3)

		while (CurrentTime := pg.time.get_ticks()) < EndTime:
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
	         CardFade=False, ScoreboardFade=False, BoardColour=False):

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

			pg.display.update()

		return ToBlit2

	def StartRound(self):
		cardnumber = self.Attributes.Round["CardNumberThisRound"]
		RoundNumber = self.Attributes.Round["RoundNumber"]

		self.TypeWriterText(
			f'{f"ROUND {RoundNumber} starting" if self.Attributes.Game["StartCardNumber"] != 1 else "Round starting"}! '
			f'This round has {cardnumber} card{"s" if cardnumber != 1 else ""}.',
			MidRound=False,
			UpdateGameSurfaceAfter=True
		)

		self.TypeWriterText(
			f'{self.Attributes.Round["RoundLeader"].name} starts this round.',
			MidRound=False,
			UpdateGameSurfaceAfter=True
		)

		if not self.Attributes.Tournament['GamesPlayed'] and self.Attributes.Round['RoundNumber'] == 1:

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

		# Tell the server we've finished typing the above.
		self.GetGame('AC')

		# Wait for the server to make a new pack of cards.
		self.Wait(Attribute='NewPack', FunctionOfGame=True, OutsideRound=True)

		self.TypeWriterText(
			f'The trumpcard for this round is the {self.Attributes.Round["TrumpCard"]}, '
			f'which has been removed from the pack.',
			MidRound=False
		)

		# Tell the server we've typed the above text.
		self.GetGame('AC')
		self.UpdateGameSurface(RoundOpening=True)

		# Wait for the server to deal cards for this round.
		self.Wait(Attribute='CardsDealt', FunctionOfGame=True, OutsideRound=True)

		# Fade in the *player text on the board only*, then the cards in your hand + the trumpcard.
		CoverRects = self.Fade('Maroon', (0, 0, 0), FadeIn=True)
		self.UpdateGameSurface(UpdateWindow=False)
		self.Fade(255, 0, List=CoverRects, TextFade=False, CardFade=True)

		self.Wait(TimeToWait=250)

		for RectTuple in CoverRects:
			RectTuple[0].set_alpha(255)

		if self.Attributes.Round["RoundNumber"] == 1 and not self.Attributes.Tournament['GamesPlayed']:
			self.TypeWriterText('Cards for this round have been dealt; each player must decide what they will bid.')

		# We need to enter our bid.
		self.Wait(
			FunctionOfGame=True,
			TypingNeeded=True,
			function=lambda x, y: x.Attributes.Tournament['gameplayers'][self.player.playerindex].Bid == -1,
			Bidding=True,
			SwitchUpdatesOffAfter=False
		)

		self.Wait(TimeToWait=100, SwitchUpdatesOnBefore=False)

		# We now need to wait until everybody else has bid.
		if any(player.Bid == -1 for player in self.gameplayers):

			self.Wait(
				FunctionOfGame=True,
				function=lambda x, y: any(player.Bid == -1 for player in x.Attributes.Tournament['gameplayers']),
				Bidding=True,
				SwitchUpdatesOffAfter=False
			)

		self.Wait(TimeToWait=100)
		self.GameUpdatesNeeded = False

		# (Refresh the board.)
		self.UpdateGameSurface(UpdateWindow=True)

		self.TypeWriterText(
			f'{"All" if self.Attributes.Tournament["PlayerNumber"] !=2 else "Both"} players have now bid.',
			WipeClean=True
		)

		RoundLeaderIndex = self.Attributes.Round["RoundLeader"].playerindex

		if AllEqual(player.Bid for player in self.gameplayers):
			BidNumber = self.gameplayers[0].Bid
			FirstWord = 'Both' if self.Attributes.Tournament['PlayerNumber'] == 2 else 'All'
			self.TypeWriterText(f'{FirstWord} players bid {BidNumber}.', WipeClean=True)
		else:
			for player in chain(self.gameplayers[RoundLeaderIndex:], self.gameplayers[:RoundLeaderIndex]):
				self.TypeWriterText(f'{player} bids {player.Bid}.', WipeClean=True)

		self.GetGame('AC')

	def PlayTrick(self):
		TrickNumber, CardNumber = self.Attributes.Trick["TrickNumber"], self.Attributes.Round["CardNumberThisRound"]
		self.GetGame(UpdateAfter=True)
		Text = f'{f"TRICK {TrickNumber} starting" if CardNumber != 1 else "TRICK STARTING"} :'
		self.TypeWriterText(Text, WipeClean=True)

		# Tell the server we're ready to play the trick.
		self.GetGame('AC', UpdateAfter=True)

		self.Wait(
			function=lambda x, y: x.Attributes.Trick['WhoseTurnPlayerIndex'] == -1,
			FunctionOfGame=True,
			SwitchUpdatesOffAfter=False
		)

		# Play the trick, wait for all players to play

		while len(self.Attributes.Trick['PlayedCards']) < self.Attributes.Tournament['PlayerNumber']:
			if self.Attributes.Trick['WhoseTurnPlayerIndex'] != self.player.playerindex:
				self.CheckForExit()
			else:
				self.HandleAllEvents(ClicksNeeded=True, TypingNeeded=False)
			self.UpdateGameSurface(UpdateWindow=True)

		self.Wait(TimeToWait=100, SwitchUpdatesOffAfter=False)

		# Wait for a signal from the server that a winner has been determined.
		self.Wait(FunctionOfGame=True, Attribute='TrickEnd')
		WinnerName = self.Attributes.Trick['Winner'].name
		Text = f'{WinnerName} won {f"trick {TrickNumber}" if CardNumber != 1 else "the trick"}!'
		self.TypeWriterText(Text, WipeClean=True)
		self.GetGame('AC')
		self.UpdateGameSurface(UpdateWindow=True)

	def EndRound(self):
		self.GetGame()
		self.BuildScoreboard('LightGrey')
		self.BlitSurface('Game', 'Scoreboard')

		# Wait for points to be awarded.
		self.Wait(Attribute='PointsAwarded', FunctionOfGame=True, OutsideRound=True)
		self.BuildScoreboard()
		self.RoundInProgressBlits()

		self.CoverRects['Trump'][0].set_alpha(0)
		self.Fade(0, 255, List=(self.CoverRects['Trump'],), FadeIn=False, TextFade=False, CardFade=True)
		self.Fade((0, 0, 0), 'Maroon', FadeIn=False)

		self.Fill('Game', 'Maroon')
		self.BlitSurface('Game', 'Scoreboard')
		self.Wait(SwitchUpdatesOnBefore=False, TimeToWait=500)
		self.TypeWriterText('Round has ended.', WipeClean=True, MidRound=False)

		if AllEqual(player.PointsThisRound for player in self.gameplayers):
			Points = self.gameplayers[0].PointsThisRound

			self.TypeWriterText(
				f'{"Both" if self.Attributes.Tournament["PlayerNumber"] == 2 else "All"} '
				f'players won {Points} point{"s" if Points != 1 else ""}.',
				WipeClean=True,
				MidRound=False
			)

		else:
			for player in sorted(self.gameplayers, key=Player.GetPointsThisRound, reverse=True):
				Text = f'{player} won {player.PointsThisRound} point{"s" if player.PointsThisRound != 1 else ""}.'
				self.TypeWriterText(Text, WipeClean=True, MidRound=False)

		if self.Attributes.Round['CardNumberThisRound'] == 1:
			self.TypeWriterText('--- END OF GAME SCORES ---', WipeClean=True, MidRound=False)

			for i, player in enumerate(sorted(self.gameplayers, key=Player.GetPoints, reverse=True)):
				Points = player.Points

				if not i and Points != self.gameplayers[i + 1].Points:
					Verb = 'leads with'
				elif i == len(self.gameplayers) - 1 and Points != self.gameplayers[i - 1].Points:
					Verb = 'brings up the rear with'
				else:
					Verb = 'has'

				Ending = "s" if Points != 1 else ""
				self.TypeWriterText(f'{player} {Verb} {Points} point{Ending}.', WipeClean=True, MidRound=False)

		self.GetGame('AC')

	def EndGame(self):
		if len(Winners := self.Attributes.Game['Winners']) > 1:
			self.TypeWriterText('Tied game!', WipeClean=True, MidRound=False)

			self.TypeWriterText(
				f'The joint winners of this game were '
				f'{", ".join(Winner.name for Winner in Winners)}, '
				f'with {self.Attributes.Game["MaxPoints"]} each!',
				WipeClean=True,
				MidRound=False
			)

		else:
			self.TypeWriterText(f'{Winners[0].name} won the game!', WipeClean=False, MidRound=False)

		self.PlayStarted = False
		self.Wait(TimeToWait=500)
		self.Fade('LightGrey', 'Maroon', TextFade=False, ScoreboardFade=True)
		self.FireworksDisplay()
		self.Wait(TimeToWait=1000, UpdateWindow=False, OutsideRound=True)
		self.Fill('Game', 'Maroon')

		# Tell the server we've finished typing the above
		self.GetGame('AC')

		if self.Attributes.Tournament['GamesPlayed']:
			self.TournamentWinners()

		self.TypeWriterText(
			'Press the spacebar to play again with the same players, or close the window to exit the game.',
			MidRound=False)

		self.Wait(Attribute='NewGameReset', FunctionOfGame=True, OutsideRound=True, TypingNeeded=True)
		self.Surfaces['BaseScoreboard'] = None
		self.GetGame('AC')
		self.Surfaces['Hand'].RectList.clear()
		self.CoverRects['Hand'].clear()

	def FireworksDisplay(self):
		# This part of the code adapted from code by Adam Binks
		# Fade to black
		self.Fade('Maroon', (0, 0, 0), TextFade=False, BoardColour=True)

		# every frame blit a low alpha black surf so that all effects fade out slowly
		Duration = self.FireworkSettings['SecondsDuration'] * 1000
		StartTime = LastFirework = pg.time.get_ticks()
		EndTime = StartTime + Duration
		RandomAmount = random.randint(*self.FireworkSettings['Bounds'])
		x, y = self.Dimensions['Window']

		# FIREWORK LOOP (adapted from code by Adam Binks)
		while (Time := pg.time.get_ticks()) < EndTime or len(Particle.allParticles):
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

			pg.display.update()

		self.Fade((0, 0, 0), 'Maroon', TextFade=False, BoardColour=True)

	def TournamentWinners(self):
		# Wait for server to update the tournament leaderboard.
		self.Wait(Attribute='TournamentLeaders', FunctionOfGame=True, UpdateWindow=False, OutsideRound=True)
		MaxGamesWon = self.Attributes.Tournament["MaxGamesWon"]
		TournamentLeaders = self.Attributes.Tournament["TournamentLeaders"]
		SortedGameplayers = sorted(self.gameplayers, reverse=True, key=Player.GetGamesWon)

		for p, player in enumerate(SortedGameplayers):

			self.TypeWriterText(
				f'{"In this tournament, " if not p else ""}{player} '
				f'has {"also " if p and player.GamesWon == SortedGameplayers[p - 1].GamesWon else ""}'
				f'won {player.GamesWon} game{"s" if player.GamesWon != 1 else ""} so far.',
				WipeClean=True,
				MidRound=False,
				PreGame=True
			)

		GamesWonText = f'having won {MaxGamesWon} game{"s" if MaxGamesWon > 1 else ""}'

		if (WinnerNumber := len(TournamentLeaders)) == 1:
			TournamentText = f'{TournamentLeaders[0]} leads so far in this tournament, {GamesWonText}!'

		elif WinnerNumber == 2:
			Leader1, Leader2 = TournamentLeaders[0], TournamentLeaders[1]
			TournamentText = f'{Leader1} and {Leader2} lead so far in this tournament, {GamesWonText} each!'

		else:
			JoinedList = ", ".join(leader.name for leader in TournamentLeaders[:-1])
			Last = TournamentLeaders[-1]
			TournamentText = f'{JoinedList} and {Last} lead so far in this tournament, {GamesWonText} each!'

		self.TypeWriterText(TournamentText, MidRound=False, WipeClean=True, PreGame=True)


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
