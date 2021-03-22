from __future__ import annotations

from random import randint
from functools import lru_cache
from typing import TYPE_CHECKING
from queue import Queue
from collections import deque

from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin

from src.display.knock_surfaces.game_surf import GameSurface
from src.display.knock_surfaces.scoreboard_surf import Scoreboard
from src.display.knock_surfaces.trump_card_surf import TrumpCardSurface
from src.display.knock_surfaces.hand_surf import HandSurface
from src.display.knock_surfaces.board_surf import BoardSurface

from src.display.fireworks.firework_vars import FireworkVars
from src.display.fireworks.particle import Particle

from src.display.typewriter import Typewriter
from src.display.text_input import TextInput
from src.display.faders import Fader, OpacityFader
from src.display.error_tracker import Errors
from src.display.input_context import InputContext
from src.display.mouse.mouse import Mouse
from src.display.matplotlib_scoreboard import InteractiveScoreboard

from src.network.network_client import Client
from src.game.client_game import ClientGame as Game
from src.players.players_client import ClientPlayer as Player
from src.misc import GetLogger

from os import environ, path
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from pygame import (quit as pg_quit,
                    locals as pg_locals,
                    display as pg_display)

from pygame.image import load as pg_image_load
from pygame.time import Clock, delay, get_ticks as GetTicks
from pygame.mouse import set_cursor, get_pressed as pg_mouse_get_pressed
from pygame.event import get as pg_event_get
from pygame.key import get_mods as pg_key_get_mods

if TYPE_CHECKING:
	from pygame.event import Event
	from src.special_knock_types import BlitsList, DimensionTuple, OptionalDisplayManager, Colour


@lru_cache
def ZoomInHelper(
		NewVar: int,
		OldVar: int,
		ScreenSize: DimensionTuple,
		index: int
):

	if NewVar > (s := ScreenSize[index]):
		NewVar = s
	return NewVar, (NewVar != OldVar)


@lru_cache
def ZoomOutHelper(NewVar: int,
                  OldVar: int):

	if NewVar < 10:
		NewVar = 10
	return NewVar, (NewVar != OldVar)


def ControlKeyDown():
	return pg_key_get_mods() & pg_locals.KMOD_CTRL


# Subclasses DictLike for easy attribute access in the main client script

class DisplayManager:
	__slots__ = 'BoardSurf', 'ScoreboardSurf', 'HandSurf', 'TrumpCardSurf', 'InputContext', 'GameSurf', 'WindowX',\
	            'WindowY', 'ScreenX', 'ScreenY', 'Window', 'WindowIcon', 'Fullscreen',  'DeactivateVideoResize', \
	            'Mouse', 'Errors', 'FireworkVars', 'UserInput', 'Typewriter', 'client', 'DisplayUpdatesCompleted', \
	            'LastDisplayLog', 'WindowCaption', 'InteractiveScoreboard', 'Scrollwheel', 'clock', 'player', 'game', \
	            'ControlKeyFunctions', 'ArrowKeyFunctions', 'log'

	MinGameWidth = 1186
	MinGameHeight = 588
	DefaultMaxWidth = 1300
	DefaultMaxHeight = 680

	PygameIconFilePath = path.join('Images', 'PygameIcon.png')
	DefaultWindowCaption = 'Knock (made by Alex Waygood)'
	ConnectionBrokenCaption = 'LOST CONNECTION WITH THE SERVER'

	FrameRate = 100
	WindowResizeKeys = (pg_locals.K_ESCAPE, pg_locals.K_TAB)
	GameRematchKeys = (pg_locals.K_SPACE, pg_locals.K_RETURN)
	ArrowKeys = (pg_locals.K_UP, pg_locals.K_DOWN, pg_locals.K_LEFT, pg_locals.K_RIGHT)
	OnlyDisplayManager: OptionalDisplayManager = None

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	# This is so the displayManager instance can be accessed in the clientside_gameplay thread.
	def __new__(
			cls,
			playerindex: int,
			FrozenState: bool,
			StartColour: Colour
	):
		# noinspection PyDunderSlots,PyUnresolvedReferences
		cls.OnlyDisplayManager = super(DisplayManager, cls).__new__(cls)
		return cls.OnlyDisplayManager

	def __init__(
			self,
			playerindex: int,
			FrozenState: bool,
			StartColour: Colour
	):

		try:
			# Try to calculate the size of the client's computer screen
			from screeninfo import get_monitors
			Monitor = get_monitors()[0]
			WindowX, WindowY = self.WindowX, self.WindowY = Monitor.width, Monitor.height
		except:
			WindowX, WindowY = self.WindowX, self.WindowY = self.DefaultMaxWidth, self.DefaultMaxHeight

		self.player = Player.player(playerindex)
		self.game = Game.OnlyGame
		self.clock = Clock()
		self.LastDisplayLog = 0
		self.DisplayUpdatesCompleted = 0
		self.Fullscreen = True  # Technically incorrect, but it fills up the whole screen.
		self.DeactivateVideoResize = False
		self.client = Client.OnlyClient
		self.WindowCaption = 'INITIALISING, PLEASE WAIT...'

		self.ScreenX = WindowX
		self.ScreenY = WindowY

		# Must be done before initialising any Knock surfaces
		Fader.AddColourScheme()

		# The GameSurf Adds itself as a class variable to the SurfaceCoordinator in __init__
		self.GameSurf = GameSurface(StartColour, WindowX, WindowY, self.MinGameWidth, self.MinGameHeight)
		SurfaceCoordinator.AddClassVars(self.player)
		TextBlitsMixin.AddTextFader()

		self.BoardSurf = BoardSurface()  # Adds itself as a class variable to the SurfaceCoordinator in __init__
		self.ScoreboardSurf = Scoreboard()
		self.HandSurf = HandSurface()
		self.TrumpCardSurf = TrumpCardSurface()
		SurfaceCoordinator.NewWindowSize2()

		self.InputContext = InputContext()
		self.Typewriter = Typewriter([], -1, Queue(), None, None)
		self.UserInput = TextInput('', None, self.InputContext)
		self.Errors = Errors(deque(), [], GetTicks(), None)
		self.Mouse = Mouse(None, self.InputContext)
		self.Scrollwheel = self.Mouse.Scrollwheel
		self.GameSurf.scrollwheel = self.Mouse.Scrollwheel
		self.FireworkVars = FireworkVars()
		self.InteractiveScoreboard = InteractiveScoreboard(self.InputContext)
		self.WindowIcon = pg_image_load(self.PygameIconFilePath)
		self.log = GetLogger(FrozenState)

		self.ControlKeyFunctions = {
			pg_locals.K_c: self.GameSurf.MoveToCentre,
			pg_locals.K_q: self.QuitGame,
			pg_locals.K_s: self.InteractiveScoreboard.save,
			pg_locals.K_t: self.InteractiveScoreboard.show,
			pg_locals.K_v: self.UserInput.PasteEvent,
			pg_locals.K_BACKSPACE: self.UserInput.ControlBackspaceEvent,
			pg_locals.K_PLUS: self.ZoomIn,
			pg_locals.K_EQUALS: self.ZoomIn,
			pg_locals.K_MINUS: self.ZoomOut,
			pg_locals.K_UNDERSCORE: self.ZoomOut
		}

		self.ArrowKeyFunctions = {
			pg_locals.K_UP: self.GameSurf.NudgeUp,
			pg_locals.K_DOWN: self.GameSurf.NudgeDown,
			pg_locals.K_LEFT: self.GameSurf.NudgeLeft,
			pg_locals.K_RIGHT: self.GameSurf.NudgeRight
		}

	def Run(self):
		self.log.debug('Launching pygame window.')
		pg_display.set_icon(self.WindowIcon)
		self.InitialiseWindow(pg_locals.RESIZABLE)
		self.RestartDisplay()
		self.InitialiseWindow(pg_locals.RESIZABLE)
		set_cursor(pg_locals.SYSTEM_CURSOR_WAIT)
		SurfaceCoordinator.AddSurfs()
		self.GameSurf.GetSurf()
		self.WindowCaption = self.DefaultWindowCaption
		pg_display.set_caption(self.WindowCaption)

		self.log.debug('Starting main pygame loop.')
		while True:
			self.Update()

	def InitialiseScoreboard(self):
		self.ScoreboardSurf.RealInit()

	def GetHandRects(self):
		self.HandSurf.GetHandRects()

	def ClearHandRects(self):
		self.HandSurf.ClearRectList()

	def ActivateHand(self):
		self.HandSurf.Activate()

	def DeactivateHand(self):
		self.HandSurf.Deactivate()

	def Blits(self, L: BlitsList):
		self.GameSurf.surf.blits(L)

	def GameInitialisationFade(self):
		if not self.game.GamesPlayed:
			self.GameSurf.FillFade('MenuScreen', 'GamePlay', 1000)

		self.ScoreboardSurf.Activate()
		self.ScoreboardSurf.FillFade('GamePlay', 'Scoreboard', 1000)

	def RoundStartFade(self):
		self.BoardSurf.Activate()
		self.TrumpCardSurf.Activate()

		TextBlitsMixin.TextFade('GamePlay', 'Black', 1000)
		self.HandSurf.Activate()
		OpacityFader.CardFade(('HandCardFade', 'TrumpCardFade'), 1000, FadeIn=True)

	@staticmethod
	def TrickEndFade():
		OpacityFader.CardFade(('BoardCardFade',), 300, FadeIn=False)

	def RoundEndFade(self):
		self.HandSurf.Deactivate()

		OpacityFader.CardFade(('TrumpCardFade',), 1000, FadeIn=False)
		TextBlitsMixin.TextFade('Black', 'GamePlay', 1000)

		self.TrumpCardSurf.Deactivate()
		self.BoardSurf.Deactivate()

	def FireworksSequence(self):
		# Fade the screen out incrementally to prepare for the fireworks display
		self.ScoreboardSurf.FillFade('Scoreboard', 'GamePlay', 1000)
		self.GameSurf.FillFade('GamePlay', 'Black', 1000)

		self.ScoreboardSurf.Deactivate()

		# This part of the code adapted from code by Adam Binks
		FireworkVars.LastFirework = GetTicks()
		Duration = self.FireworkVars.SecondsDuration * 1000
		FireworkVars.EndTime = self.FireworkVars.LastFirework + Duration
		FireworkVars.RandomAmount = randint(*self.FireworkVars.Bounds)

		with self.InputContext(FireworksInProgress=True):
			delay(Duration)
			while GetTicks() < FireworkVars.EndTime or Particle.allParticles:
				delay(100)

		# Fade the screen back to maroon after the fireworks display.
		self.GameSurf.FillFade('Black', 'GamePlay', 1000)
		delay(1000)

	def QuitGame(self):
		self.log.debug('Quitting game.')
		pg_quit()
		raise Exception('Game has ended.')

	def Update(self):
		self.clock.tick(self.FrameRate)
		Condition = (Player.number() != self.game.PlayerNumber and self.game.StartPlay)

		if Condition or not pg_display.get_init() or not pg_display.get_surface():
			self.QuitGame()

		pg_display.update()
		NewGameInfo, BrokenConnection = self.client.Update()

		if BrokenConnection and self.WindowCaption != self.ConnectionBrokenCaption:
			pg_display.set_caption(self.ConnectionBrokenCaption)
			self.WindowCaption = self.ConnectionBrokenCaption

		elif not self.client.ConnectionBroken and self.WindowCaption == self.ConnectionBrokenCaption:
			pg_display.set_caption(self.DefaultWindowCaption)
			self.WindowCaption = self.DefaultWindowCaption

		if NewGameInfo:
			self.log.debug(f'Obtained new message from Client, {NewGameInfo}.')

			if NewGameInfo != 'pong':
				with self.game as g:
					g.UpdateFromServer(NewGameInfo, self.player.playerindex)

				self.log.debug('Client-side game successfully updated.')

		self.Window.fill(self.GameSurf.colour)
		# Calling Update() on the GameSurf itself calls Update() on all other surfs
		self.Window.blit(*self.GameSurf.Update())

		for event in pg_event_get():
			self.HandleEvent(event, event.type)

		self.DisplayUpdatesCompleted += 1

		if (Time := GetTicks()) > self.LastDisplayLog + 1000:
			self.LastDisplayLog = Time
			self.log.debug(f'{self.DisplayUpdatesCompleted} display updates completed.')

		if BrokenConnection:
			delay(500)

	def NewWindowSize(
			self,
			EventKey: int = 0,
			ToggleFullscreen: bool = False,
			WindowDimensions: DimensionTuple = None
	):
		self.log.debug(f'NewWindowSize(ToggleFullscreen={ToggleFullscreen}, WindowDimensions={WindowDimensions}).')

		if EventKey == pg_locals.K_ESCAPE and not self.Fullscreen:
			return None

		InitialiseArg = pg_locals.RESIZABLE

		if ToggleFullscreen:
			self.WindowX, self.WindowY = self.ScreenX, self.ScreenY
			self.DeactivateVideoResize = True

			if self.Fullscreen:
				self.WindowX, self.WindowY = (self.ScreenX - 100), (self.ScreenY - 100)
				self.RestartDisplay()
			else:
				self.WindowX, self.WindowY = self.ScreenX, self.ScreenY
				InitialiseArg = pg_locals.FULLSCREEN

			self.Fullscreen = not self.Fullscreen
		else:
			self.WindowX, self.WindowY = WindowDimensions

		self.InitialiseWindow(InitialiseArg)
		SurfaceCoordinator.NewWindowSize(self.WindowX, self.WindowY, (ToggleFullscreen and self.Fullscreen))

		for surf in (self.HandSurf, self.BoardSurf, self.TrumpCardSurf):
			surf.UpdateCardRects(ForceUpdate=True)

	# noinspection PyAttributeOutsideInit
	def InitialiseWindow(self, flags: int):
		self.Window = pg_display.set_mode((self.WindowX, self.WindowY), flags=flags)
		self.Window.fill(self.GameSurf.colour)
		pg_display.update()

	def RestartDisplay(self):
		pg_display.quit()
		pg_display.init()
		pg_display.set_caption(self.WindowCaption)
		pg_display.set_icon(self.WindowIcon)

	def ZoomIn(self):
		if self.Fullscreen:
			return None

		x, y = self.WindowX, self.WindowY
		a, b = (x + 20), (y + 20)

		if a >= self.ScreenX and b >= self.ScreenY:
			self.NewWindowSize(ToggleFullscreen=True)
			return None

		x, ResizeNeeded1 = ZoomInHelper(a, x, (self.ScreenX, self.ScreenY), 0)
		y, ResizeNeeded2 = ZoomInHelper(b, y, (self.ScreenX, self.ScreenY), 1)

		if ResizeNeeded1 or ResizeNeeded2:
			self.NewWindowSize(WindowDimensions=(x, y), ToggleFullscreen=False)

	def ZoomOut(self):
		x, y = self.WindowX, self.WindowY

		if x == y == 10:
			return None

		a, b = (x - 20), (y - 20)

		x, ResizeNeeded1 = ZoomOutHelper(a, x)
		y, ResizeNeeded2 = ZoomOutHelper(b, y)

		if ResizeNeeded1 or ResizeNeeded2:
			self.NewWindowSize(WindowDimensions=(x, y), ToggleFullscreen=self.Fullscreen)

	def VideoResizeEvent(self, NewSize: DimensionTuple):
		# Videoresize events are triggered on exiting/entering fullscreen as well as manual resizing;
		# we only want it to be triggered after a manual resize.

		if self.DeactivateVideoResize:
			self.DeactivateVideoResize = False
		else:
			self.NewWindowSize(WindowDimensions=NewSize)

	def HandleEvent(
			self,
			event: Event,
			EvType: int
	):
		if EvType == pg_locals.QUIT:
			self.QuitGame()

		elif EvType == pg_locals.KEYDOWN:
			if self.Scrollwheel.IsDown:
				self.Scrollwheel.ComesUp()

			elif (EvKey := event.key) in self.WindowResizeKeys:
				self.NewWindowSize(EvKey, ToggleFullscreen=True)

			elif ControlKeyDown():
				try:
					self.ControlKeyFunctions[EvKey]()
				except KeyError:
					self.KeyDownEvents(event, EvKey)

			else:
				self.KeyDownEvents(event, EvKey)

		elif EvType == pg_locals.VIDEORESIZE:
			self.VideoResizeEvent(event.size)

		elif EvType == pg_locals.MOUSEBUTTONDOWN:
			Button = event.button

			# pushing the scrollwheel down will click the scrollwheel, no matter what else is going on
			if Button == 2:
				self.Scrollwheel.clicked()

			# if the scrollwheel is down, any button on the mouse being pushed will cause it to come up.
			elif self.Scrollwheel.IsDown:
				self.Scrollwheel.ComesUp()

			# This only applies if it ISN'T  scrollwheel press and the scrollwheel is NOT currently down.
			elif not self.InputContext.FireworksDisplay:
				if ControlKeyDown():
					if Button == 4:
						self.ZoomIn()
					elif Button == 5:
						self.ZoomOut()
					elif not self.client.ConnectionBroken and Button == 1 and not pg_mouse_get_pressed(5)[2]:
						self.Mouse.click = True

				elif Button == 4:
					self.GameSurf.NudgeUp()

				elif Button == 5:
					self.GameSurf.NudgeDown()

				# Whether or not clicks are needed is tested in the Gameplay Loop function
				elif not self.client.ConnectionBroken and Button == 1 and not pg_mouse_get_pressed(5)[2]:
					self.Mouse.click = True

		elif not self.InputContext.FireworksDisplay:
			if EvType == pg_locals.MOUSEBUTTONUP:
				if (Button := event.button) == 1 and not self.client.ConnectionBroken:
					self.Mouse.click = False
				elif Button == 2 and GetTicks() > self.Scrollwheel.OriginalDownTime + 1000:
					self.Scrollwheel.ComesUp()

			elif EvType == pg_locals.MOUSEMOTION and pg_mouse_get_pressed(5)[0] and pg_mouse_get_pressed(5)[2]:
				self.GameSurf.MouseMove(event.rel)

	def KeyDownEvents(
			self,
			event: Event,
			EvKey: int
	):

		if not self.InputContext.FireworksDisplay and EvKey in self.ArrowKeys:
			self.ArrowKeyFunctions[EvKey]()

		elif not self.client.ConnectionBroken:
			if self.InputContext.GameReset and EvKey in self.GameRematchKeys:
				self.game.RepeatGame = True
				self.client.QueueMessage('@1')
			elif EvKey == pg_locals.K_BACKSPACE:
				self.UserInput.NormalBackspaceEvent()
			elif EvKey == pg_locals.K_RETURN:
				self.HandleTextInput(self.UserInput.EnterEvent())
			else:
				self.UserInput.AddTextEvent(event.unicode)

	def HandleTextInput(self, Input: str):
		if not Input:
			return None

		if isinstance(self.player.name, int):
			if len(Input) < 30:
				# Don't need to check that letters are ASCII-compliant;
				# wouldn't have been able to type them if they weren't.
				self.player.name = Input
				self.client.QueueMessage(f'@P{Input}{self.player.playerindex}')
			else:
				self.Errors.Add('Name must be <30 characters; please try again.')

		elif not (self.game.StartCardNumber or self.player.playerindex):
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			try:
				assert 1 <= float(Input) <= self.game.MaxCardNumber and float(Input).is_integer()
				self.game.StartCardNumber = int(Input)
				self.client.QueueMessage(f'@N{Input}')
			except:
				self.Errors.Add(f'Please enter an integer between 1 and {self.game.MaxCardNumber}')

		elif self.player.Bid == -1:
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			Count = len(self.player.Hand)

			try:
				assert 0 <= float(Input) <= Count and float(Input).is_integer()
				self.player.Bid = int(Input)
				self.client.QueueMessage(''.join((f'@B', f'{f"{Input}" : 0>2}', f'{self.player.playerindex}')))
			except:
				self.Errors.Add(f'Your bid must be an integer between 0 and {Count}.')

	def __repr__(self):
		return f'''Object for managing all variables related to pygame display on the client-side of the game. Current state:
-MinGameWidth: {self.MinGameWidth}
-MinGameHeight: {self.MinGameHeight}
-DefaultMaxWidth = {self.DefaultMaxWidth}
-DefaultMaxHeight = {self.DefaultMaxHeight}
-PygameIconFilePath: {self.PygameIconFilePath} (absolute: {path.abspath(self.PygameIconFilePath)}).
-Fullscreen: {self.Fullscreen}.
-DeactivateVideoResize: {self.DeactivateVideoResize}
-ScreenX: {self.ScreenX}.
-ScreenY: {self.ScreenY}.
-Fonts: {SurfaceCoordinator.Fonts}.
-Colourscheme: [[\n\n{SurfaceCoordinator.ColourScheme}]].
-FireworkVars: [[\n\n{self.FireworkVars}]].
-WindowMargin: {SurfaceCoordinator.WindowMargin}.
-CardX: {SurfaceCoordinator.CardX}
-CardY: {SurfaceCoordinator.CardY}
-BoardCentre: {SurfaceCoordinator.BoardCentre}
-PlayStartedInputPos: {SurfaceCoordinator.PlayStartedInputPos}
-PreplayInputPos: {SurfaceCoordinator.PreplayInputPos}

'''
