from __future__ import annotations

from random import randint
from functools import lru_cache
from typing import TYPE_CHECKING
from queue import Queue
from collections import deque
from logging import getLogger

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
from src.display.faders import OpacityFader, ColourFader
from src.display.error_tracker import Errors
from src.display.input_context import InputContext
from src.display.mouse.mouse import Mouse
from src.display.interactive_scoreboard import InteractiveScoreboard

from src.network.client_class import Client
from src.data_structures import DictLike

from os import environ, path
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

from pygame import (locals as pg_locals,
                    display as pg_display)

from pygame.image import load as pg_image_load
from pygame.time import delay, get_ticks as GetTicks
from pygame.mouse import set_cursor

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList, DimensionTuple
	from src.players.players_client import ClientPlayer as Player


log = getLogger(__name__)


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


# Subclasses DictLike for easy attribute access in the main client script

class DisplayManager(DictLike):
	__slots__ = 'BoardSurf', 'ScoreboardSurf', 'HandSurf', 'TrumpCardSurf', 'InputContext', 'GameSurf', 'WindowX',\
	            'WindowY', 'ScreenX', 'ScreenY', 'Window', 'WindowIcon', 'Fullscreen',  'DeactivateVideoResize', \
	            'Mouse', 'Errors', 'FireworkVars', 'UserInput', 'Typewriter', 'client', 'FrozenState', \
	            'DisplayUpdatesCompleted', 'LastDisplayLog', 'WindowCaption', 'InteractiveScoreboard'

	MinGameWidth = 1186
	MinGameHeight = 588
	DefaultMaxWidth = 1300
	DefaultMaxHeight = 680
	PygameIconFilePath = path.join('Images', 'PygameIcon.png')
	DefaultWindowCaption = 'Knock (made by Alex Waygood)'
	ConnectionBrokenCaption = 'LOST CONNECTION WITH THE SERVER'

	def __init__(
			self,
			player: Player,
			FrozenState: bool
	):

		try:
			# Try to calculate the size of the client's computer screen
			from screeninfo import get_monitors
			Monitor = get_monitors()[0]
			WindowX, WindowY = self.WindowX, self.WindowY = Monitor.width, Monitor.height
		except:
			WindowX, WindowY = self.WindowX, self.WindowY = self.DefaultMaxWidth, self.DefaultMaxHeight

		self.FrozenState = FrozenState
		self.LastDisplayLog = 0
		self.DisplayUpdatesCompleted = 0
		self.Fullscreen = True  # Technically incorrect, but it fills up the whole screen.
		self.DeactivateVideoResize = False
		self.client = Client.OnlyClient
		self.WindowCaption = 'INITIALISING, PLEASE WAIT...'

		self.ScreenX = WindowX
		self.ScreenY = WindowY
		# The GameSurf Adds itself as a class variable to the SurfaceCoordinator in __init__
		self.GameSurf = GameSurface(WindowX, WindowY, self.MinGameWidth, self.MinGameHeight)
		SurfaceCoordinator.AddClassVars(player)
		ColourFader.AddColourScheme()

		self.BoardSurf = BoardSurface()  # Adds itself as a class variable to the SurfaceCoordinator in __init__
		self.ScoreboardSurf = Scoreboard()
		self.HandSurf = HandSurface()
		self.TrumpCardSurf = TrumpCardSurface()
		SurfaceCoordinator.NewWindowSize2()

		self.InputContext = InputContext()
		self.Typewriter = Typewriter([], -1, Queue(), None, None)
		self.UserInput = TextInput('', None, self.InputContext)
		self.Errors = Errors(deque(), [], GetTicks(), None)
		self.Mouse = Mouse(None)
		self.GameSurf.scrollwheel = self.Mouse.Scrollwheel
		self.FireworkVars = FireworkVars()
		self.InteractiveScoreboard = InteractiveScoreboard(self.InputContext)

		self.WindowIcon = pg_image_load(self.PygameIconFilePath)
		pg_display.set_icon(self.WindowIcon)
		log.debug('Launching pygame window.')
		self.InitialiseWindow(pg_locals.RESIZABLE)
		self.RestartDisplay()
		self.InitialiseWindow(pg_locals.RESIZABLE)
		self.Window.fill(self.GameSurf.colour)
		pg_display.update()
		set_cursor(pg_locals.SYSTEM_CURSOR_WAIT)
		SurfaceCoordinator.AddSurfs()
		self.GameSurf.GetSurf()
		self.WindowCaption = self.DefaultWindowCaption
		pg_display.set_caption(self.WindowCaption)

	def InitialiseScoreboard(self):
		self.ScoreboardSurf.RealInit()

	def Blits(self, L: BlitsList):
		self.GameSurf.surf.blits(L)

	def GameInitialisationFade(self, GamesPlayed: int):
		if not GamesPlayed:
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

	def Update(self):
		if self.client.ConnectionBroken and self.WindowCaption != self.ConnectionBrokenCaption:
			pg_display.set_caption(self.ConnectionBrokenCaption)
			self.WindowCaption = self.ConnectionBrokenCaption
		elif not self.client.ConnectionBroken and self.WindowCaption == self.ConnectionBrokenCaption:
			pg_display.set_caption(self.DefaultWindowCaption)
			self.WindowCaption = self.DefaultWindowCaption

		self.Window.fill(self.GameSurf.colour)
		# Calling Update() on the GameSurf itself calls Update() on all other surfs
		self.Window.blit(*self.GameSurf.Update())
		self.Mouse.UpdateCursor()
		pg_display.update()

		self.DisplayUpdatesCompleted += 1

		if (Time := GetTicks()) > self.LastDisplayLog + 1000:
			self.LastDisplayLog = Time
			log.debug(f'{self.DisplayUpdatesCompleted} display updates completed.')

	def NewWindowSize(self,
	                  EventKey: int = 0,
	                  ToggleFullscreen: bool = False,
	                  WindowDimensions: DimensionTuple = None):

		log.debug(f'NewWindowSize(ToggleFullscreen={ToggleFullscreen}, WindowDimensions={WindowDimensions}).')

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

		self.Update()

	# noinspection PyAttributeOutsideInit
	def InitialiseWindow(self, flags: int):
		self.Window = pg_display.set_mode((self.WindowX, self.WindowY), flags=flags)

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
