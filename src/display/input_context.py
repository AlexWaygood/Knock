"""A context manager for aiding communication between threads."""

from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar
from src.config import game
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.surface_coordinator import SurfaceCoordinator

if TYPE_CHECKING:
	from src.special_knock_types import ExitArg1, ExitArg2, ExitArg3

# noinspection PyTypeChecker
IC = TypeVar('IC', bound='GameInputContextManager')


class GameInputContextManager(TextBlitsMixin, SurfaceCoordinator):
	"""Context manager to allow for elegant communication between threads.
	Only one instance of this class is ever created, although this is not enforced through a "singleton" pattern.

	This class keeps track of:
		-   Whether any user input is expected of the client at this point in the game,
			whether in the form of mouse clicks or keyboard input.
		-   Whether a fireworks display is currently in progress.
		-   Whether there is currently a static message being displayed to the client (and the font of that message).

	"""

	__slots__ = (
		'trick_click_needed', 'click_to_start', 'typing_needed', 'game_updates_needed', 'static_message_to_user',
		'message_font', 'game_reset', 'fireworks_display'
	)

	def __init__(self, /) -> None:
		self()
		self.all_surfaces.append(self)

	@property
	def input_needed(self, /) -> bool:
		"""Return `True` if any clicks or typing is required from the user at this point in the game, else `False`"""
		return self.typing_needed or self.click_to_start or self.trick_click_needed

	@property
	def clicks_needed(self, /) -> bool:
		"""Return `True` if any clicks are required from the user at this point in the game, else `False`"""
		return self.click_to_start or self.trick_click_needed

	# Might be passed force_update=True, so need to keep it in as an argument.
	def update(self, /, *, force_update: bool = False) -> None:
		"""Blit the message to the user (if there is one) to the appropriate point on the screen."""

		msg = self.static_message_to_user

		if not msg:
			return

		center = self.board_centre if game.play_started else self.game_surf.attrs.centre

		self.game_surf.surf.blit(
			*self.get_text_helper(msg, self.fonts[self.message_font], (0, 0, 0), center=center)
		)

	def __call__(
			self: IC,
			trick_click_needed: bool = False,
			click_to_start: bool = False,
			typing_needed: bool = False,
			game_updates_needed: bool = False,
			static_message_to_user: str = '',
			message_font: str = '',
			game_reset: bool = False,
			fireworks_display: bool = False
	) -> IC:

		self.trick_click_needed = trick_click_needed
		self.click_to_start = click_to_start
		self.typing_needed = typing_needed
		self.game_updates_needed = game_updates_needed
		self.static_message_to_user = static_message_to_user
		self.message_font = message_font
		self.game_reset = game_reset
		self.fireworks_display = fireworks_display
		return self

	def __enter__(self: IC, /) -> IC:
		return self

	def __exit__(self, exc_type: ExitArg1, exc_val: ExitArg2, exc_tb: ExitArg3) -> None:
		self()
