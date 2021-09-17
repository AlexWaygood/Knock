"""A class representing the Surface onto which the player's hand will be blitted, and a helper function."""

from __future__ import annotations
from typing import TYPE_CHECKING, Final
from functools import lru_cache
from src import Position
from src.display.abstract_surfaces import KnockSurfaceWithCards
from src.display.faders import OpacityFader
from src.config import game
from src.static_constants import CardFaderNames, OPAQUE_OPACITY_KEY

if TYPE_CHECKING:
	from src.cards.client_card import ClientCard as Card


COVER_RECT_START_OPACITY: Final = OPAQUE_OPACITY_KEY


@lru_cache
def get_hand_rects(game_surf_x: int, window_margin: int, card_x: int, start_card_number: int) -> list[Position]:
	"""Cached, pure, helper-function for calculating the rects onto which cards are to be blitted for the HandSurface."""

	x = window_margin
	double_window_margin = x * 2
	potential_buffer = card_x // 2

	width_with_potential_buffer = sum((
			(card_x * start_card_number),
			double_window_margin,
			(potential_buffer * (start_card_number - 1))
	))

	if width_with_potential_buffer < game_surf_x:
		card_buffer_in_hand = potential_buffer
	else:
		card_buffer_in_hand = min(
			x,
			((game_surf_x - double_window_margin - (card_x * start_card_number)) // (start_card_number - 1))
		)

	return [Position(x=(x + (i * (card_x + card_buffer_in_hand))), y=0) for i in range(start_card_number)]


class HandSurface(KnockSurfaceWithCards):
	"""The surface onto which the player's hand is blitted."""

	__slots__ = '_hand_rects_calculated'

	# The hand surface's Y-coordinate changes, but the X-coordinate never does
	x: Final = 0

	def __init__(self, /) -> None:
		self.card_list = self.player.hand
		self.card_update_queue = game.new_card_queues.hand

		self.card_fade_manager = OpacityFader(
			start_opacity=COVER_RECT_START_OPACITY,
			name=CardFaderNames.HAND_CARD_FADE_KEY
		)

		super().__init__()   # calls surf_dimensions()
		self._hand_rects_calculated = False

	@property
	def hand_rects_calculated(self, /) -> bool:
		"""Return `True` if the rects for the HandSurface have been calculated, else `False`."""
		return self._hand_rects_calculated

	# noinspection PyAttributeOutsideInit
	def surf_dimensions(self, /) -> None:
		"""Calculate the width, height, and y-coordinate for this surface. (The x-coordinate is set as a constant.)"""
		game_surf, card_y, window_margin = self.game_surf, self.card_y, self.window_margin
		self.y = game_surf.height - (card_y + window_margin)
		self.width = game_surf.width
		self.height = card_y + window_margin

	def get_hand_rects(self, /) -> None:
		"""Calculate the rects for blitting cards onto the HandSurface."""

		self.add_rect_list(get_hand_rects(self.width, self.window_margin, self.card_x, game.start_card_no))
		self._hand_rects_calculated = True

	def clear_rect_list(self, /) -> None:
		"""Clear the list of rects for blitting cards onto the HandSurface."""

		self.rect_list.clear()
		self.cover_rects.clear()
		self._hand_rects_calculated = False

	def update_card(self, card: Card, index: int) -> None:
		"""Update a card that has newly arrived onto this surface."""

		rect = self.rect_list[index]
		card.rect = rect
		card.collide_rect = rect.move(*self.attrs.topleft).move(*self.game_surf.attrs.topleft)

	# update, get_surf_blits & initialise methods not defined here as the base class doesn't need to be overridden.
