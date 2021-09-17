from __future__ import annotations
from functools import lru_cache
from typing import TYPE_CHECKING, NamedTuple, TypeVar, Final

from src.config import game
from src.static_constants import MiscFonts, CardFaderNames, OPAQUE_OPACITY_KEY

from src.display.abstract_surfaces import KnockSurfaceWithCards
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.faders import OpacityFader

if TYPE_CHECKING:
	from src.cards.client_card import ClientCard as Card
	from src.special_knock_types import BlitsList, Position

	# noinspection PyTypeChecker
	T = TypeVar('T', bound='TrumpCardSurfaceDimensions')


START_COVER_RECT_OPACITY: Final[str] = OPAQUE_OPACITY_KEY
TRUMPCARD_SURFACE_TITLE: Final = 'trump_card'


class TrumpCardSurfaceDimensions(NamedTuple):
	x: int
	width: int
	height: int
	trumpcard_pos: Position

	@classmethod
	@lru_cache
	def from_game_dimensions(cls: type[T], /, *, game_x: int, card_x: int, card_y: int, normal_linesize: int) -> T:
		# noinspection PyArgumentList
		return cls(
			x=(game_x - (card_x + 50)),
			width=(card_x + 2),
			height=(card_y + int(normal_linesize * 2.5) + 10),
			trumpcard_pos=(1, int(normal_linesize * 2.5))
		)


# noinspection PyAttributeOutsideInit
class TrumpCardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	__slots__ = 'font'

	def __init__(self, /) -> None:
		self.card_list = game.trump_card

		self.card_fade_manager = OpacityFader(
			start_opacity=START_COVER_RECT_OPACITY,
			name=CardFaderNames.TRUMP_CARD_FADE_KEY
		)

		self.card_update_queue = game.new_card_queues.trump_card
		super().__init__()   # Calls surf_dimensions()

	def initialise(self, /) -> TrumpCardSurface:
		self.font = self.fonts[MiscFonts.TRUMP_CARD_FONT]
		return super().initialise()

	def surf_dimensions(self, /) -> None:
		dimensions = TrumpCardSurfaceDimensions.from_game_dimensions(
			game_x=self.game_surf.width,
			card_x=self.card_x,
			card_y=self.card_y,
			normal_linesize=self.font.linesize
		)

		self.x, self.width, self.height, trump_card_pos = dimensions
		self.y = self.window_margin
		self.add_rect_list((trump_card_pos,))

	def update_card(self, card: Card, index: int) -> None:
		card.rect = self.rect_list[0]

	def get_surf_blits(self, /) -> BlitsList:
		blits_list = super().get_surf_blits()
		font, linesize = self.font, self.font.linesize
		return (
				blits_list
				+ [self.get_text(TRUMPCARD_SURFACE_TITLE, font, center=((self.attrs.centre[0] / 2), (linesize / 2)))]
		)
