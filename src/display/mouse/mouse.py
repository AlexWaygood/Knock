from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.mouse.cursors import cursors

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from src.config import game, client
from pygame.mouse import get_pressed, get_pos, set_cursor
from pygame.time import get_ticks

if TYPE_CHECKING:
	from src.special_knock_types import Position, Cursor_Type
	from src.display import GameInputContextManager


# noinspection PyPep8Naming
def scrollwheel_down_cursor(
		scrollwheel_down_x: float,
		scrollwheel_down_y: float,
		mouse_pos_x: int,
		mouse_pos_y: int,
		MAGIC_NUMBER: int = 50
) -> Cursor_Type:

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


@dataclass(eq=False, unsafe_hash=True)
class Scrollwheel:
	# Repr automatically defined as it's a dataclass!

	__slots__ = '_is_down', 'down_pos', 'down_time', 'original_down_time'

	_is_down: bool
	down_pos: Position
	down_time: int
	original_down_time: int

	@property
	def is_down(self, /) -> bool:
		return self._is_down

	def clicked(self, /) -> None:
		self._is_down = not self.is_down
		if self.is_down:
			self.down_pos = get_pos()
			self.down_time = self.original_down_time = get_ticks()

	def comes_up(self, /) -> None:
		self._is_down = False

	@property
	def is_moving(self, /) -> bool:
		return self.is_down and get_ticks() > self.original_down_time + 20

	def get_movement(self, /) -> Position:
		# noinspection PyTupleAssignmentBalance
		down_x, down_y, mouse_x, mouse_y = *self.down_pos, *get_pos()
		return ((down_x - mouse_x) / 200), ((down_y - mouse_y) / 200)


class Mouse(SurfaceCoordinator):
	__slots__ = 'scrollwheel', 'cursor', 'scoreboard_button', 'card_hover_ID', 'click', 'cards_in_hand', 'context'

	def __init__(self, /, *, scoreboard_button, context: GameInputContextManager) -> None:
		self.context = context
		self.scrollwheel = Scrollwheel(False, tuple(), 0, 0)
		self.cursor = cursors.default
		self.scoreboard_button = scoreboard_button
		self.card_hover_ID = ''
		self.click = False
		self.cards_in_hand = self.player.hand
		self.all_surfaces.append(self)

	# It might be passed force_update=True, so we can't take that argument out.
	def update(self, /, *, force_update: bool = False) -> None:
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

	def __repr__(self, /) -> str:
		return f'''Object representing current state of the mouse. Current state:
-cursor: {self.cursor}
-card_hover_ID: {self.card_hover_ID}
-click: {self.click}

'''
