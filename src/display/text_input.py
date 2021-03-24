from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING
from pyperclip import paste

from src.misc import PrintableCharactersPlusSpace
from src.display.input_context import InputContext
from src.display.abstract_text_rendering import TextBlitsMixin, GetCursor
from src.display.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.display.abstract_text_rendering import FontAndLinesize
	from src.display.error_tracker import Errors


@dataclass(eq=False)
class TextInput(TextBlitsMixin, SurfaceCoordinator):
	# Repr & hash automatically defined as it's a dataclass!
	__slots__ = 'Text', 'font', 'context', 'error_tracker'

	Text: str
	font: Optional[FontAndLinesize]
	context: InputContext
	error_tracker: Errors

	def __post_init__(self):
		self.AllSurfaces.append(self)
		self.font = self.Fonts['UserInputFont']

	def Initialise(self):
		self.font = self.Fonts['UserInputFont']
		return self

	def PasteEvent(self):
		if self.context.TypingNeeded:
			t = paste()
			try:
				assert all(letter in PrintableCharactersPlusSpace for letter in t)
				self.Text += t
			except:
				pass

	def ControlBackspaceEvent(self):
		if self.Text and self.context.TypingNeeded:
			self.Text = ' '.join(self.Text.split(' ')[:-1])

	def NormalBackspaceEvent(self):
		if self.Text and self.context.TypingNeeded:
			self.Text = self.Text[:-1]

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

	# Must define hash even though it's in the parent class, because it's a dataclass
	def __hash__(self):
		return id(self)

	def ReportError(self, message: str):
		self.error_tracker.Add(message)

	def QueueClientMessage(self, message: str):
		self.client.QueueMessage(message)

	def EnterEvent(self):
		if not (self.Text and self.context.TypingNeeded):
			return None

		if isinstance(self.player.name, int):
			if len(self.Text) < 30:
				# Don't need to check that letters are ASCII-compliant;
				# wouldn't have been able to type them if they weren't.
				self.player.name = self.Text
				self.QueueClientMessage(f'@P{self.Text}{self.player.playerindex}')
			else:
				self.ReportError('Name must be <30 characters; please try again.')

		elif not (self.game.StartCardNumber or self.player.playerindex):
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			try:
				assert 1 <= float(self.Text) <= self.game.MaxCardNumber and float(self.Text).is_integer()
				self.game.StartCardNumber = int(self.Text)
				self.QueueClientMessage(f'@N{self.Text}')
			except:
				self.ReportError(f'Please enter an integer between 1 and {self.game.MaxCardNumber}')

		elif self.player.Bid == -1:
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			Count = len(self.player.Hand)

			try:
				assert 0 <= float(self.Text) <= Count and float(self.Text).is_integer()
				self.player.Bid = int(self.Text)
				self.QueueClientMessage(''.join((f'@B', f'{f"{self.Text}" : 0>2}', f'{self.player.playerindex}')))
			except:
				self.ReportError(f'Your bid must be an integer between 0 and {Count}.')

		self.Text = ''
