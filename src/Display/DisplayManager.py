import random

from functools import lru_cache
from typing import Sequence

from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator
from src.Display.AbstractSurfaces.TextRendering import TextBlitsMixin
from src.Display.KnockSurfaces.GameSurf import GameSurface
from src.Display.KnockSurfaces.ScoreboardSurf import Scoreboard
from src.Display.KnockSurfaces.TrumpCardSurf import TrumpCardSurface
from src.Display.KnockSurfaces.HandSurf import HandSurface
from src.Display.KnockSurfaces.BoardSurf import BoardSurface
from src.Display.Typewriter import Typewriter
from src.Display.TextInput import TextInput
from src.Display.Faders import OpacityFader, ColourFader
from src.Display.ErrorTracker import Errors
from src.Display.InputContext import InputContext
from src.Display.ColourScheme import ColourScheme

from src.Display.Fireworks.FireworkVars import FireworkVars
from src.Display.Fireworks.FireworkParticle import Particle

from src.DataStructures import DictLike
from src.Display.Mouse.Mouse import Mouse

from os import environ, path
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
import pygame.display as display
from pygame.time import get_ticks as GetTicks
from pygame.time import delay


def RestartDisplay():
	display.quit()
	display.init()


@lru_cache
def ResizeHelper(var1, var2, ScreenSize, i):
	"""
	@type var1: int
	@type var2: int
	@type ScreenSize: tuple[int, int]
	@type i: int
	"""

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

	def __init__(self, Theme, game, player):
		"""
		@type Theme: str
		@type game: src.Game.ClientGame.ClientGame
		@type player: src.Players.ClientPlayers.ClientPlayer
		"""

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

		self.WindowIcon = pg.image.load(path.join('../../Images/Cards', 'PygameIcon.png'))
		self.InitialiseWindow(pg.RESIZABLE)
		RestartDisplay()
		self.InitialiseWindow(pg.RESIZABLE)

		MinWidth, MinHeight = self.MinGameWidth, self.MinGameHeight
		self.GameSurf = GameSurface(colours.MenuScreen, WindowX, WindowY, MinWidth, MinHeight)
		SurfaceCoordinator.AddClassVars(game, player, colours, self.GameSurf)
		ColourFader.AddColourScheme(colours)

		# Default placeholder value for the ScoreboardSurf
		self.BoardSurf = BoardSurface()
		self.ScoreboardSurf = None
		self.HandSurf = HandSurface()
		self.TrumpCardSurf = TrumpCardSurface()

		SurfaceCoordinator.BoardSurf = self.BoardSurf
		SurfaceCoordinator.NewWindowSize2()

		self.InputContext = InputContext()
		self.Typewriter = Typewriter()
		self.UserInput = TextInput('', None, self.InputContext)
		self.Errors = Errors()
		self.Mouse = Mouse(None)
		self.GameSurf.scrollwheel = self.Mouse.Scrollwheel
		self.FireworkVars = FireworkVars()

	def InitialiseScoreboard(self):
		self.ScoreboardSurf = Scoreboard()

	def Blits(self, L: Sequence):
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

	def NewWindowSize(self, ToggleFullscreen=False, WindowDimensions=None):
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
	def InitialiseWindow(self, flags):
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
