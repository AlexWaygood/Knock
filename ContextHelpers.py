from SurfaceBaseClasses import FixedTextBlitsMixin


class ContextHelper(object):
	def __init__(self, **kwargs):
		pass

	def __call__(self, **kwargs):
		self.__init__(**kwargs)
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.__init__()
		return self


class InputContext(ContextHelper, FixedTextBlitsMixin):
	__slots__ = 'TrickClickNeeded', 'ClickToStart', 'TypingNeeded', 'GameUpdatesNeeded', 'Text', 'font', \
	            'GameReset', 'FireworksDisplay'

	def __init__(self, TrickClickNeeded=False, ClickToStart=False, TypingNeeded=False, GameUpdatesNeeded=False,
	             Message='', font='', GameReset=False, FireworksDisplay=False, **kwargs):

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

	def GetMessage(self, fontdict, center):
		return self.GetPresetText(fontdict[self.font], center=center) if self.Text else []


class FadeContext(ContextHelper):
	__slots__ = 'Hand', 'BoardCards', 'TrumpCard', 'BoardColour', 'Scoreboard'

	def __init__(self, Hand=False, BoardCards=False, BoardColour=False, Scoreboard=False, TrumpCard=False, **kwargs):
		super().__init__(**kwargs)
		self.Hand = Hand
		self.BoardCards = BoardCards
		self.TrumpCard = TrumpCard
		self.BoardColour = BoardColour
		self.Scoreboard = Scoreboard


class Contexts(object):
	__slots__ = 'Fades', 'Input'

	def __init__(self):
		self.Input = InputContext()
		self.Fades = FadeContext()


class Sendable(object):
	__slots__ = 'value'

	def __init__(self):
		super().__init__()
		self.value = True

	def __enter__(self):
		self.value = False

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.value = True

	def __bool__(self):
		return self.value
