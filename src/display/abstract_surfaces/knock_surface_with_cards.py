from __future__ import annotations

from typing import TYPE_CHECKING, Optional, NamedTuple, TypeVar
from src.static_constants import FillColours
from src.display.abstract_surfaces.knock_surface import KnockSurface
from functools import lru_cache
from abc import abstractmethod

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame import Surface, Rect

if TYPE_CHECKING:
	from src.special_knock_types import Position, BlitsList, PositionSequence
	from src.cards.client_card import ClientCard as Card
	RectList = list[Optional[Rect]]
	# noinspection PyTypeChecker
	C = TypeVar('C', bound='CoverRect')


class CoverRect(NamedTuple):
	surf: Surface
	rect: Rect

	@property
	def surfandpos(self: C) -> C:
		return self

	def __hash__(self) -> int:
		return id(self)


CoverRectList = list[CoverRect]


# noinspection PyAttributeOutsideInit
class KnockSurfaceWithCards(KnockSurface):
	__slots__ = 'rect_list', 'card_list', 'cover_rects', 'card_fade_manager', 'card_update_queue', 'colour'

	def __init__(self) -> None:
		self.colour = self.colour_scheme[FillColours.GAMEPLAY_FILL_COLOUR]
		self.rect_list: RectList = []
		self.cover_rects: CoverRectList = []
		super().__init__()

	# Static method, but kept in this namespace for lrucaching reasons
	@lru_cache
	def rect_list_helper(
			self,
			card_x: int,
			card_y: int,
			*card_positions: Position
	) -> tuple[RectList, CoverRectList]:

		a = [Rect(p[0], p[1], card_x, card_y) for p in card_positions]
		b = [CoverRect(Surface((card_x, card_y)), rect) for rect in a]
		return a, b

	def add_rect_list(self, card_positions: PositionSequence) -> None:
		self.rect_list, self.cover_rects = self.rect_list_helper(self.card_x, self.card_y, *card_positions)

		for cv in self.cover_rects:
			cv.surf.set_alpha(self.card_fade_manager.opacity())

	def fill(self) -> None:
		self.surf.fill(self.colour)

		for cv in self.cover_rects:
			cv.surf.fill(self.colour)

		if (FadeOpacity := self.card_fade_manager.fade_in_progress()) is not False:
			for cv in self.cover_rects:
				cv.surf.set_alpha(FadeOpacity)

	def get_surf_blits(self) -> BlitsList:
		self.update_card_rects()
		blits_list = [card.surfandpos for card in self.card_list]

		if self.card_fade_manager and self.card_list:
			blits_list += [cv.surfandpos for cv in self.cover_rects[:len(self.card_list)]]

		return blits_list

	def update_card_rects(self, /, force_update: bool = False) -> None:
		update_needed = False

		if not self.card_update_queue.empty():
			update_needed = True
			self.card_update_queue.get()

		if update_needed or force_update:
			for i, card in enumerate(self.card_list):
				self.update_card(card, i)

	@abstractmethod
	def update_card(self, card: Card, index: int) -> None: ...
