from __future__ import annotations

import random

from functools import lru_cache
from typing import TYPE_CHECKING, Optional
from queue import Queue
from collections import deque

from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin
from src.display.knock_surfaces.game_surf import GameSurface
from src.display.knock_surfaces.scoreboard_surf import Scoreboard
from src.display.knock_surfaces.trump_card_surf import TrumpCardSurface
from src.display.knock_surfaces.hand_surf import HandSurface
from src.display.knock_surfaces.board_surf import BoardSurface
from src.display.typewriter import Typewriter
from src.display.text_input import TextInput
from src.display.faders import OpacityFader, ColourFader
from src.display.error_tracker import Errors
from src.display.input_context import InputContext
from src.display.colour_scheme import ColourScheme

from src.display.fireworks.firework_vars import FireworkVars
from src.display.fireworks.particle import Particle

from src.data_structures import DictLike
from src.display.mouse.mouse import Mouse

from os import environ, path
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
import pygame.display as display
from pygame.time import get_ticks as GetTicks
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import Position, BlitsList
	from src.game.client_game import ClientGame as Game
	from src.players.players_client import ClientPlayer as Player


def RestartDisplay():
	display.quit()
	display.init()


@lru_cache
def ResizeHelper(var1: int,
                 var2: int,
                 ScreenSize: Position,
                 i: int):

	var1 = ScreenSize[i] if var1 > ScreenSize[i] else var1
	var1 = 10 if var1 < 10 else var1
	ResizeNeeded = (var1 != var2)
	var2 = var1
	return var2, ResizeNeeded


class DisplayManager(DictLike):
	__slots__ = 'BoardSurf', 'ScoreboardSurf', 'HandSurf', 'TrumpCardSurf', 'InputContext', 'GameSurf', 'WindowX',\
	            'WindowY', 'ScreenX', 'ScreenY', 'Window', 'WindowIcon', 'Fullscreen',  'DeactivateVideoResize', \
	            'Mouse', 'Errors', 'FireworkVars', 'UserInput', 'Typewriter'

	MinGameWidth = 1186
	MinGameHeight = 588
	DefaultMaxWidth = 1300
	DefaultMaxHeight = 680
	PygameIconFilePath = path.join('Images', 'Cards', 'PygameIcon.png')

	def __init__(
			self,
			Theme: str,
			game: Game,
			player: Player
	):

		try:
			# Try to calculate the size of the client's computer screen
			from screeninfo import get_monitors
			Monitor = get_monitors()[0]
			WindowX, WindowY = self.WindowX, self.WindowY = Monitor.width, Monitor.height
		except:
			WindowX, WindowY = self.WindowX, self.WindowY = self.DefaultMaxWidth, self.DefaultMaxHeight

		self.Fullscreen = False
		self.DeactivateVideoResize = False

		self.ScreenX = WindowX
		self.ScreenY = WindowY
		colours = ColourScheme(Theme)

		self.WindowIcon = pg.image.load(self.PygameIconFilePath)

		self.InitialiseWindow(pg.RESIZABLE)
		RestartDisplay()
		self.InitialiseWindow(pg.RESIZABLE)

		MinWidth, MinHeight = self.MinGameWidth, self.MinGameHeight
		self.GameSurf = GameSurface(colours.MenuScreen, WindowX, WindowY, MinWidth, MinHeight)
		SurfaceCoordinator.AddClassVars(game, player, colours, self.GameSurf)
		ColourFader.AddColourScheme(colours)

		# Default placeholder value for the ScoreboardSurf
		self.BoardSurf = BoardSurface()
		self.ScoreboardSurf: Optional[Scoreboard] = None
		self.HandSurf = HandSurface()
		self.TrumpCardSurf = TrumpCardSurface()

		SurfaceCoordinator.BoardSurf = self.BoardSurf
		SurfaceCoordinator.NewWindowSize2()

		self.InputContext = InputContext()
		self.Typewriter = Typewriter([], -1, Queue(), None, None)
		self.UserInput = TextInput('', None, self.InputContext)
		self.Errors = Errors(deque(), [], GetTicks(), None)
		self.Mouse = Mouse(None)
		self.GameSurf.scrollwheel = self.Mouse.Scrollwheel
		self.FireworkVars = FireworkVars()

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

	def InitialiseScoreboard(self):
		self.ScoreboardSurf = Scoreboard()

	def Blits(self, L: BlitsList):
		self.GameSurf.attrs.surf.blits(L)

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
		FireworkVars.RandomAmount = random.randint(*self.FireworkVars.Bounds)

		with self.InputContext(FireworksInProgress=True):
			delay(Duration)
			while GetTicks() < FireworkVars.EndTime or Particle.allParticles:
				delay(100)

		# Fade the screen back to maroon after the fireworks display.
		self.GameSurf.FillFade('Black', 'GamePlay', 1000)
		delay(1000)

	def Update(self):
		# Calling Update() on the GameSurf itself calls Update() on all other surfs
		self.Window.fill(self.GameSurf.colour)
		self.Window.blit(*self.GameSurf.Update())
		display.update()

	def NewWindowSize(self,
	                  ToggleFullscreen: bool = False,
	                  WindowDimensions: Position = None):

		WindowX, WindowY, InitialiseArg = self.ScreenX, self.ScreenY, pg.RESIZABLE

		if ToggleFullscreen:
			self.DeactivateVideoResize = True

			if self.Fullscreen:
				WindowX, WindowY = (self.ScreenX - 100), (self.ScreenY - 100)
				RestartDisplay()
			else:
				WindowX, WindowY = WindowDimensions
				InitialiseArg = pg.FULLSCREEN

			self.Fullscreen = not self.Fullscreen

		self.InitialiseWindow(InitialiseArg)
		SurfaceCoordinator.NewWindowSize(WindowX, WindowY, (ToggleFullscreen and self.Fullscreen))

		for surf in (self.HandSurf, self.BoardSurf, self.TrumpCardSurf):
			surf.UpdateCardRects(ForceUpdate=True)

		self.Update()

	# noinspection PyAttributeOutsideInit
	def InitialiseWindow(self, flags: int):
		display.set_caption('Knock (made by Alex Waygood)')
		display.set_icon(self.WindowIcon)
		self.Window = display.set_mode((self.WindowX, self.WindowY), flags=flags)

	def ZoomWindow(self, Button: int):
		x, y = self.WindowX, self.WindowY

		if (self.Fullscreen and Button in (4, pg.K_PLUS)) or (Button in (5, pg.K_MINUS) and x == 10 and y == 10):
			return None

		a, b = ((x + 20), (y + 20)) if Button in (4, pg.K_PLUS) else ((x - 20), (y - 20))

		if a >= self.ScreenX and b >= self.ScreenY:
			self.Fullscreen = True
			self.NewWindowSize(ToggleFullscreen=True)
			return None

		FromFullScreen = self.Fullscreen
		self.Fullscreen = False
		x, ResizeNeeded1 = ResizeHelper(a, x, (self.ScreenX, self.ScreenY), 0)
		y, ResizeNeeded2 = ResizeHelper(b, y, (self.ScreenX, self.ScreenY), 1)

		if ResizeNeeded1 or ResizeNeeded2:
			self.NewWindowSize(WindowDimensions=(x, y), ToggleFullscreen=FromFullScreen)

	def VideoResizeEvent(self, event: pg.event.Event):
		# Videoresize events are triggered on exiting/entering fullscreen as well as manual resizing;
		# we only want it to be triggered after a manual resize.

		if self.DeactivateVideoResize:
			self.DeactivateVideoResize = False
		else:
			self.NewWindowSize(WindowDimensions=event.size)
