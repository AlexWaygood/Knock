from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from pyperclip import copy, paste

from src.Misc_locals import PrintableCharactersPlusSpace
from src.display.input_context import InputContext
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin, GetCursor
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import K_RETURN, K_BACKSPACE, KMOD_CTRL, K_v
from pygame.key import get_mods as pg_key_get_mods

if TYPE_CHECKING:
	from src.display.abstract_surfaces.text_rendering import FontAndLinesize
	from pygame.event import Event


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
		if event.key == K_v and (pg_key_get_mods() & KMOD_CTRL):
			t = paste()
			try:
				assert all(letter in PrintableCharactersPlusSpace for letter in t)
				self.Text += t
			except:
				copy(t)
			return None

		if (EvUnicode := event.unicode) in PrintableCharactersPlusSpace:
			try:
				self.Text += EvUnicode
			finally:
				return None

		if self.Text:
			if (EvKey := event.key) == K_BACKSPACE:
				if pg_key_get_mods() & KMOD_CTRL:
					self.Text = ' '.join(self.Text.split(' ')[:-1])
				else:
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
		self.GameSurf.surf.blits(GetCursor(L, self.font))

	def __hash__(self):
		return hash(repr(self))
