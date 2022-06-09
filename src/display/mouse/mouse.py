"""Classes representing the mouse and scrollwheel."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar
from dataclasses import dataclass
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.mouse.cursors import cursors

from src import DataclassyReprBase, Position, Vector
from src.config import game, client
from pygame.mouse import get_pressed, get_pos, set_cursor
from pygame.time import get_ticks

if TYPE_CHECKING:
	from src.special_knock_types import Cursor_Type
	from src.display import GameInputContextManager


# noinspection PyPep8Naming
def scrollwheel_down_cursor(
		scrollwheel_down_x: float,
		scrollwheel_down_y: float,
		mouse_pos_x: int,
		mouse_pos_y: int,
		MAGIC_NUMBER: int = 50
) -> Cursor_Type:
	"""Given that the mouse is moving, get the cursor representing the current direction of travel of the mouse."""

	if mouse_pos_x < (scrollwheel_down_x - MAGIC_NUMBER):
		if mouse_pos_y < (scrollwheel_down_y - MAGIC_NUMBER):
			return cursors.northwest
		if mouse_pos_y > (scrollwheel_down_y + MAGIC_NUMBER):
			return cursors.southwest
		return cursors.west

	if mouse_pos_x > (scrollwheel_down_x + MAGIC_NUMBER):
		if mouse_pos_y < (scrollwheel_down_y - MAGIC_NUMBER):
			return cursors.northeast
		if mouse_pos_y > (scrollwheel_down_y + MAGIC_NUMBER):
			return cursors.southeast
		return cursors.east

	if mouse_pos_y > (scrollwheel_down_y + MAGIC_NUMBER):
		return cursors.south
	if mouse_pos_y < (scrollwheel_down_y - MAGIC_NUMBER):
		return cursors.north
	return cursors.diamond


@dataclass(eq=False, unsafe_hash=True, repr=False)
class Scrollwheel(DataclassyReprBase):
	"""The scrollwheel."""

	__slots__ = {
		'down_pos': '(Position): The position at which the scrollwheel was when it was pressed down',
		'down_time': '(int): The time at which the scrollwheel was initially pressed down (if it is currently down)',
		'_is_down': '(bool): A private attribute indicating whether the scrollwheel is down or not'
	}

	NON_REPR_SLOTS: ClassVar = '_is_down',
	EXTRA_REPR_ATTRS: ClassVar = 'is_down', 'is_moving'

	down_pos: Position
	down_time: int

	def __post_init__(self) -> None:
		self._is_down = False

	@property
	def is_down(self, /) -> bool:
		"""Return `True` if the scrollwheel is currently being pressed down, else `False`."""
		return self._is_down

	def clicked(self, /) -> None:
		"""Click the scrollwheel.

		Modifies
		--------
		self.is_down (a property that cannot be set directly)
		self.down_pos (only modified if the scrollwheel is going down, not modified if it is coming up)
		self.down_time (only modified if the scrollwheel is going down, not modified if it is coming up)
		"""

		self._is_down = not self.is_down
		if self.is_down:
			self.down_pos = Position(*get_pos())
			self.down_time = get_ticks()

	def comes_up(self, /) -> None:
		"""Modify internal state to register that the scrollwheel has come up.

		Modifies
		--------
		self.is_down (a property that cannot be set directly)
		"""
		self._is_down = False

	@property
	def is_moving(self, /) -> bool:
		"""Return `True` if the scrollwheel has been down for >20 milliseconds."""
		return self.is_down and get_ticks() > self.down_time + 20

	def get_movement(self, /) -> Vector:
		"""Return the amount by which the mouse has moved since the scrollwheel initially went down.

		Returns
		-------
		Vector: an (x, y) tuple indicating the amount by which the mouse has moved.
		"""

		# noinspection PyTupleAssignmentBalance
		down_x, down_y, mouse_x, mouse_y = *self.down_pos, *get_pos()
		return Vector(((down_x - mouse_x) / 200), ((down_y - mouse_y) / 200))


class Mouse(SurfaceCoordinator, DataclassyReprBase):
	"""A computer mouse."""

	__slots__ = {
		'scrollwheel': "The mouse's scrollwheel",
		'cursor': "The current cursor representing the mouse on the screen",
		'scoreboard_button': "The button that can be clicked on the screen in order to launch a matplotlib window",
		'card_hover_ID': "The ID of the card that the mouse is currently over (if it is over one)",
		'click': "`True` if the mouse has just been clicked, else `False`",
		'cards_in_hand': "The list of cards in the player's hand at present",
		'context': "The global context manager for the game."
	}

	NON_REPR_SLOTS = 'scoreboard_button', 'cards_in_hand', 'context'
	EXTRA_REPR_ATTRS = 'cursor_value',

	def __init__(self, /, *, scoreboard_button, context: GameInputContextManager) -> None:
		self.context = context
		self.scrollwheel = Scrollwheel(down_pos=Position(0, 0), down_time=0)
		self.cursor = cursors.default
		self.scoreboard_button = scoreboard_button
		self.card_hover_ID = ''
		self.click = False
		self.cards_in_hand = self.player.hand
		self.all_surfaces.append(self)

	# It might be passed force_update=True, so we can't take that argument out.
	def update(self, /, *, force_update: bool = False) -> None:
		"""Update the mouse."""

		if (cur := self.cursor_value) != self.cursor:
			self.cursor = cur
			set_cursor(*cur)

		if self.click:
			if self.context.click_to_start:
				game.time_to_start()

			elif (
					self.context.trick_click_needed
					and self.cursor == 'hand'
					and self.player.pos_in_trick == len(game.played_cards)
			):
				game.execute_play(self.card_hover_ID, self.player.player_index)

	@property
	def cursor_value(self, /) -> Cursor_Type:
		"""Get the cursor currently representing the mouse on the screen."""

		if client.connection_broken:
			return cursors.wait

		mouse_pos = get_pos()

		if self.scrollwheel.is_down:
			return scrollwheel_down_cursor(*self.scrollwheel.down_pos, *mouse_pos)

		if get_pressed(5)[0] and get_pressed(5)[2]:  # or self.scoreboard_button.colliderect.collidepoint(*MousePos))
			return cursors.hand

		condition = all((
			self.cards_in_hand,
			game.trick_in_progress,
			game.whose_turn_playerindex == self.player.player_index
		))

		if not condition:
			return cursors.default

		cur = cursors.default
		for card in self.cards_in_hand:
			if card.colliderect.collidepoint(*mouse_pos):
				self.card_hover_ID = repr(card)
				cur = cursors.hand

				if PlayedCards := game.played_cards:
					suit_led = PlayedCards[0].Suit
					condition = any(UnplayedCard.Suit == suit_led for UnplayedCard in self.cards_in_hand)

					if card.Suit != suit_led and condition:
						cur = cursors.illegal_move
		return cur
