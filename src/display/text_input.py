from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from src.printable_characters import PrintableCharactersPlusSpace
from src.display.input_context import InputContext
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin, GetCursor
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.display.abstract_surfaces.text_rendering import FontAndLinesize
	from pygame.event import Event

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import K_RETURN, K_BACKSPACE


@dataclass
class TextInput(TextBlitsMixin, SurfaceCoordinator):
	# Repr automatically defined as it's a dataclass!

	__slots__ = 'Text', 'font', 'InputContext'

	Text: str
	font: Optional[FontAndLinesize]
	InputContext: InputContext

	def __post_init__(self):
		self.AllSurfaces.append(self)
		self.font = self.Fonts['UserInputFont']

	def Initialise(self):
		self.font = self.Fonts['UserInputFont']

	def AddInputText(self, event: Event):
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

	# Need to keep **kwargs in as it might be passed ForceUpdate=True
	def Update(self, **kwargs):
		if not self.InputContext.TypingNeeded:
			return None

		with self.game as g:
			PlayStarted = g.StartPlay

		center = self.PlayStartedInputPos if PlayStarted else self.PreplayInputPos
		L = [self.GetTextHelper(self.Text, self.font, (0, 0, 0), center=center)] if self.Text else center
		self.GameSurf.attrs.surf.blits(GetCursor(L, self.font))

	def __hash__(self):
		return hash(repr(self))
