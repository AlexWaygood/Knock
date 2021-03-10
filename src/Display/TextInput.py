from dataclasses import dataclass

from src.PrintableCharacters import PrintableCharactersPlusSpace
from src.Display.InputContext import InputContext
from src.Display.AbstractSurfaces.TextRendering import TextBlitsMixin, GetCursor
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import K_RETURN, K_BACKSPACE


@dataclass
class TextInput(TextBlitsMixin, SurfaceCoordinator):
	__slots__ = 'Text', 'font', 'InputContext'

	Text: str
	font: None
	InputContext: InputContext

	def __post_init__(self):
		self.AllSurfaces.append(self)

	def Initialise(self):
		self.font = self.Fonts['UserInputFont']

	def AddInputText(self, event):
		"""
		@type event: pygame.event.Event
		"""

		if (EvUnicode := event.unicode) in PrintableCharactersPlusSpace:
			try:
				self.Text += EvUnicode
			finally:
				return None

		elif not self.Text:
			return None

		if (EvKey := event.key) == K_BACKSPACE:
			self.Text = self.Text[:-1]

		elif EvKey == K_RETURN:
			Text = self.Text
			self.Text = ''
			return Text

	def Update(self, ForceUpdate=False):
		if not self.InputContext.TypingNeeded:
			return None

		with self.game as g:
			PlayStarted = g.PlayStarted

		center = self.PlayStartedInputPos if PlayStarted else self.PreplayInputPos
		L = self.GetTextHelper(self.Text, self.font, (0, 0, 0), center=center) if self.Text else []
		self.GameSurf.attrs.surf.blits(GetCursor(L, self.font))
