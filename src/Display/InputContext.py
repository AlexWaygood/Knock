from src.Display.AbstractSurfaces.TextRendering import TextBlitsMixin
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator


class InputContext(TextBlitsMixin, SurfaceCoordinator):
	__slots__ = 'TrickClickNeeded', 'ClickToStart', 'TypingNeeded', 'GameUpdatesNeeded', 'Text', 'font', 'GameReset', \
	            'FireworksDisplay'

	def __init__(self, TrickClickNeeded=False, ClickToStart=False, TypingNeeded=False, GameUpdatesNeeded=False,
	             Message='', font='', GameReset=False, FireworksDisplay=False, **kwargs):

		"""
		@type TrickClickNeeded: bool
		@type ClickToStart: bool
		@type TypingNeeded: bool
		@type GameUpdatesNeeded: bool
		@type Message: str
		@type font: str
		@type GameReset: bool
		@type FireworksDisplay: bool
		"""

		super().__init__(**kwargs)
		assert bool(Message) == bool(font), 'Must specify both message and font, or neither'

		self.TrickClickNeeded = TrickClickNeeded
		self.ClickToStart = ClickToStart
		self.TypingNeeded = TypingNeeded
		self.GameUpdatesNeeded = GameUpdatesNeeded
		self.Text = Message
		self.font = font
		self.GameReset = GameReset
		self.FireworksDisplay = FireworksDisplay

	def InputNeeded(self):
		return self.TypingNeeded or self.ClickToStart or self.TrickClickNeeded

	def ClicksNeeded(self):
		return self.ClickToStart or self.TrickClickNeeded

	def Update(self, ForceUpdate=False):
		if not self.Text:
			return None

		center = self.BoardCentre if self.game.StartPlay else self.GameSurf.attrs.centre
		self.GameSurf.attrs.surf.blit(self.GetTextHelper(self.Text, self.Fonts[self.font], (0, 0, 0), center=center))

	def __call__(self, **kwargs):
		self.__init__(**kwargs)
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__init__()
		return self
