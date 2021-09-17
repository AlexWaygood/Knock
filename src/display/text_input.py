from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar, Final
from pyperclip import paste

from src.config import game, client
from src.static_constants import USER_INPUT_FONT, PRINTABLE_CHARACTERS_PLUS_SPACE
from src.display import GameInputContextManager, TextBlitsMixin, get_cursor, SurfaceCoordinator

if TYPE_CHECKING:
	from src.special_knock_types import OptionalFont
	from src.display import Errors

	# noinspection PyTypeChecker
	T = TypeVar('T', bound='TextInput')


TEXT_COLOUR: Final = (0, 0, 0)
MAX_PLAYER_NAME_LENGTH: Final = 30


# noinspection PyBroadException
@dataclass(eq=False)
class TextInput(TextBlitsMixin, SurfaceCoordinator):
	# Repr & hash automatically defined as it's a dataclass!
	__slots__ = 'Text', 'font', 'context', 'error_tracker'

	text: str
	font: OptionalFont
	context: GameInputContextManager
	error_tracker: Errors

	def __post_init__(self) -> None:
		self.all_surfaces.append(self)
		self.font = self.fonts[USER_INPUT_FONT]

	def initialise(self: T, /) -> T:
		self.font = self.fonts[USER_INPUT_FONT]
		return self

	def paste_event(self, /) -> None:
		if self.context.typing_needed:
			t = paste()
			with suppress(BaseException):
				assert all(letter in PRINTABLE_CHARACTERS_PLUS_SPACE for letter in t)
				self.text += t

	def control_backspace_event(self, /) -> None:
		if self.text and self.context.typing_needed:
			self.text = ' '.join(self.text.split(' ')[:-1])

	def normal_backspace_event(self, /) -> None:
		if self.text and self.context.typing_needed:
			self.text = self.text[:-1]

	def add_text_event(self, event_unicode: str) -> None:
		if self.context.typing_needed and event_unicode in PRINTABLE_CHARACTERS_PLUS_SPACE:
			with suppress(BaseException):
				self.text += event_unicode

	# Need to keep **kwargs in as it might be passed force_update=True
	def update(self, **kwargs) -> None:
		if self.context.typing_needed:
			with game as g:
				play_started = g.play_started

			center = self.play_started_input_pos if play_started else self.preplay_input_pos

			if self.text:
				blits_list = [self.get_text_helper(self.text, self.font, TEXT_COLOUR, center=center)]
			else:
				blits_list = center

			self.game_surf.surf.blits(get_cursor(blits_list, self.font))

	# Must define hash even though it's in the parent class, because it's a dataclass
	def __hash__(self) -> int:
		return id(self)

	def report_error(self, message: str) -> None:
		self.error_tracker.add(message)

	def queue_client_message(self, message: str) -> None:
		client.queue_message(message)

	def enter_event(self) -> None:
		if not (self.text and self.context.typing_needed):
			return None

		if isinstance(self.player.name, int):
			if len(self.text) < MAX_PLAYER_NAME_LENGTH:
				# Don't need to check that letters are ASCII-compliant;
				# wouldn't have been able to type them if they weren't.
				self.player.name = self.text
				self.queue_client_message(f'@P{self.text}{self.player.player_index}')
			else:
				self.report_error(f'Name must be <{MAX_PLAYER_NAME_LENGTH} characters; please try again.')

		elif not (game.start_card_no or self.player.player_index):
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			try:
				if not (1 <= float(self.text) <= game.max_card_number and float(self.text).is_integer()):
					raise TypeError('No.')

				game.start_card_no = int(self.text)
				self.queue_client_message(f'@N{self.text}')
			except BaseException:
				self.report_error(f'Please enter an integer between 1 and {game.max_card_number}')

		elif self.player.bid == -1:
			# Using try/except rather than if/else to catch unexpected errors as well as expected ones.
			count = len(self.player.hand)

			try:
				if not (0 <= float(self.text) <= count and float(self.text).is_integer()):
					raise TypeError('No')

				self.player.bid = int(self.text)
				self.queue_client_message(''.join((f'@B', f'{f"{self.text}" : 0>2}', f'{self.player.player_index}')))
			except BaseException:
				self.report_error(f'Your bid must be an integer between 0 and {count}.')

		self.text = ''
