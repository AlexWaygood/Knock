from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Optional, Final
from fractions import Fraction

from src.config import client

from src.display.colours import ColourScheme
from src.display.abstract_text_rendering import Fonts

from src.cards.client_card import ClientCard as Card
from src import Position, Dimensions
from src.get_dimensions import get_dimensions

if TYPE_CHECKING:
	from src.players.players_client import ClientPlayer as Players
	from src.display import GameSurface, BoardSurface


# noinspection PyTypeChecker
S = TypeVar('S', bound='SurfaceCoordinator')
INPUT_POS_OFFSET: Final = 50


class SurfaceCoordinator:
	__slots__ = tuple()

	player: Optional[Players] = None
	game_surf: Optional[GameSurface] = None  # Will add itself as a class attribute in its own __init__()
	board_surf: Optional[BoardSurface] = None  # Will add itself as a class attribute in its own __init__()
	fonts: Optional[Fonts] = None
	colour_scheme: Optional[ColourScheme] = None
	player_no = 0

	window_margin = 0
	card_x = 0
	card_y = 0
	required_resize_ratio: Optional[Fraction] = None

	board_centre: Position = tuple()
	play_started_input_pos: Position = tuple()
	preplay_input_pos: Position = tuple()

	all_surfaces: list[SurfaceCoordinator] = []

	@classmethod
	def add_class_vars(cls, /, *, player: Players) -> None:
		cls.colour_scheme = ColourScheme.OnlyColourScheme
		cls.player = player
		cls.game_surf.hand = cls.player.hand
		game_x, game_y = cls.game_surf.dimensions
		cls.fonts = Fonts(game_x, game_y)
		cls.window_margin, cls.card_x, cls.card_y, cls.required_resize_ratio = get_dimensions(game_x, game_y)

	@classmethod
	def add_surfs(cls, /) -> None:
		for surf in cls.all_surfaces:
			surf.get_surf()

	@classmethod
	def new_window_size_1(cls, /) -> None:
		game_x, game_y = cls.game_surf.dimensions

		cls.window_margin, cls.card_x, cls.card_y, RequiredResizeRatio = get_dimensions(
			game_x,
			game_y,
			current_card_dimensions=Dimensions(cls.card_x, cls.card_y)
		)

		Card.update_images(RequiredResizeRatio)
		cls.fonts.__init__(*cls.game_surf.dimensions)

	@classmethod
	def new_window_size_2(cls, /) -> None:
		for surf in cls.all_surfaces:
			surf.initialise().get_surf()

		cls.board_centre = BoardX, BoardY = cls.board_surf.nonrelative_board_centre
		cls.play_started_input_pos = Position(BoardX, (BoardY + INPUT_POS_OFFSET))

		cls.preplay_input_pos = Position(
			cls.game_surf.attrs.centre[0],
			(cls.game_surf.attrs.centre[1] + INPUT_POS_OFFSET)
		)

	@classmethod
	def new_window_size(cls, /, *, window_dimensions: Dimensions, reset_pos: bool) -> None:

		cls.game_surf.new_window_size(*window_dimensions, reset_pos)
		cls.new_window_size_1()
		cls.new_window_size_2()

	@classmethod
	def update_all(cls, /, *, force_update: bool = False) -> None:
		if not client.connection_broken:
			for surf in cls.all_surfaces:
				surf.update(force_update=force_update)

	def initialise(self: S, /) -> S:
		return self

	def update(self, /, *, force_update: bool = False) -> None:
		pass

	def get_surf(self, /) -> None:
		pass
