from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from pyperclip import copy, paste

from src.misc import PrintableCharactersPlusSpace
from src.display.input_context import InputContext
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin, GetCursor
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.display.abstract_surfaces.text_rendering import FontAndLinesize


@dataclass(eq=False, unsafe_hash=True)
class TextInput(TextBlitsMixin, SurfaceCoordinator):
	# Repr & hash automatically defined as it's a dataclass!

	__slots__ = 'Text', 'font', 'context'

	Text: str
	font: Optional[FontAndLinesize]
	context: InputContext

	def __post_init__(self):
		self.AllSurfaces.append(self)
		self.font = self.Fonts['UserInputFont']

	def Initialise(self):
		self.font = self.Fonts['UserInputFont']

	def PasteEvent(self):
		if self.context.TypingNeeded:
			t = paste()
			try:
				assert all(letter in PrintableCharactersPlusSpace for letter in t)
				self.Text += t
			except:
				copy(t)

	def ControlBackspaceEvent(self):
		if self.Text and self.context.TypingNeeded:
			self.Text = ' '.join(self.Text.split(' ')[:-1])

	def NormalBackspaceEvent(self):
		if self.Text and self.context.TypingNeeded:
			self.Text = self.Text[:-1]

	def EnterEvent(self):
		if self.Text and self.context.TypingNeeded:
			Text = self.Text
			self.Text = ''
			return Text

	def AddTextEvent(self, EventUnicode: str):
		if self.context.TypingNeeded and EventUnicode in PrintableCharactersPlusSpace:
			try:
				self.Text += EventUnicode
			except:
				pass

	# Need to keep **kwargs in as it might be passed ForceUpdate=True
	def Update(self, **kwargs):
		if self.context.TypingNeeded:
			with self.game as g:
				PlayStarted = g.StartPlay

			center = self.PlayStartedInputPos if PlayStarted else self.PreplayInputPos
			L = [self.GetTextHelper(self.Text, self.font, (0, 0, 0), center=center)] if self.Text else center
			self.GameSurf.surf.blits(GetCursor(L, self.font))
