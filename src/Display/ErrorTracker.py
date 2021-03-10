from fractions import Fraction
from collections import deque
from functools import lru_cache

from src.Display.AbstractSurfaces.TextRendering import TextBlitsMixin
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import get_ticks as GetTicks


@lru_cache
def ErrorPosHelper(GameX, GameY):
	"""
	@type GameX: int
	@type GameY: int
	"""

	return int(GameX * Fraction(550, 683)), int(GameY * Fraction(125, 192))


class Errors(TextBlitsMixin, SurfaceCoordinator):
	__slots__ = 'Messages', 'ThisPass', 'StartTime', 'Pos', 'Title', 'TitleFont', 'MessageFont'

	def __init__(self):
		self.AllSurfaces.append(self)
		self.Messages = deque()
		self.ThisPass = []
		self.StartTime = GetTicks()
		self.Initialise()
		self.Title = None

	# noinspection PyAttributeOutsideInit
	def Initialise(self):
		self.Pos = ErrorPosHelper(self.GameSurf.Width, self.GameSurf.Height)
		self.TitleFont = self.Fonts['ErrorTitleFont']
		self.MessageFont = self.Fonts['ErrorMessagesFont']

	def Update(self, ForceUpdate=False):
		self.ErrorMessages()

		if self.Messages and GetTicks() > self.StartTime + 5000:
			self.Messages.clear()

		while len(self.Messages) > 5:
			self.Messages.popleft()

		self.GameSurf.attrs.surf.blits(self.Messages)

	def ErrorMessages(self):
		if not self.ThisPass:
			return None

		self.StartTime = GetTicks()
		Name = name if isinstance((name := self.player.name), str) else 'player'

		if not self.Messages:
			if not self.Title:
				self.Title = self.GetText(f'Messages to {Name}:', self.TitleFont, center=self.Pos)

			self.Messages = [self.Title]
			y = self.Pos[1] + self.MessageFont.linesize

		else:
			y = self.Messages[-1][1].y + self.MessageFont.linesize

		x = self.Pos[0]

		for Error in self.ThisPass:
			self.Messages.append(self.GetText(Error, self.MessageFont, center=(x, y)))
			y += self.MessageFont.linesize
