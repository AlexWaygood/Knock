from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, NamedTuple
from functools import lru_cache

from src.config import game
from src.static_constants import BoardSurfFonts, OPAQUE_OPACITY_KEY

from src.config import player_number
from src.display.abstract_surfaces import KnockSurfaceWithCards
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.faders import OpacityFader
from src import Position
from src.players.players_client import BoardTextArgs, ClientPlayer as Players

if TYPE_CHECKING:
	from src.cards.client_card import ClientCard as Card
	from src.special_knock_types import BlitsList
	PositionList = list[Position]
	# noinspection PyTypeChecker
	B = TypeVar('B', bound='BoardSurface')

# Dictates the opacity of the board_surf's cover_rects at the start of the game
COVER_RECT_START_OPACITY = OPAQUE_OPACITY_KEY


class BoardDimensions(NamedTuple):
	"""Return type for `board_dimensions_helper`"""
	card_rects_on_board: PositionList
	player_text_positions: PositionList


@lru_cache
def board_dimensions_helper(
		surf_width: int,
		surf_height: int,
		card_x: int,
		card_y: int,
		normal_linesize: int,
		player_no=player_number
) -> BoardDimensions:

	board_fifth = surf_height // 5

	triple_linesize = 3 * normal_linesize
	two_fifths_board, three_fifths_board = (board_fifth * 2), (board_fifth * 3)
	half_card_width, double_card_width = (card_x // 2), (card_x * 2)

	player_text_positions = [
		Position(card_x, int(two_fifths_board - triple_linesize)),
		Position((surf_width - card_x), int(two_fifths_board - triple_linesize))
	]

	# Top-left position & top-right position
	card_rects_on_board = [
		Position((card_x + half_card_width), (player_text_positions[0][1] - half_card_width)),
		Position((surf_width - (double_card_width + 60)), (player_text_positions[1][1] - half_card_width))
	]

	if player_no != 2:
		board_mid = surf_width // 2

		if player_no != 4:
			# Top-middle position
			player_text_positions.insert(1, Position(board_mid, (normal_linesize // 2)))

			card_rects_on_board.insert(
				1,
				Position((board_mid - half_card_width), (player_text_positions[1][1] + (normal_linesize * 4)))
			)

		if player_no != 3:
			# Bottom-right position
			player_text_positions.append(Position((surf_width - card_x), three_fifths_board))
			card_rects_on_board.append(
				Position((surf_width - (double_card_width + 60)), (player_text_positions[-1][1] - half_card_width))
			)

			# Bottom-mid position
			if player_no != 4:
				player_text_positions.append(Position(board_mid, int(surf_height - (normal_linesize * 5))))
				card_rects_on_board.append(Position(
					(board_mid - half_card_width),
					(player_text_positions[-1][1] - card_y - normal_linesize)
				))

			# Bottom-left position
			if player_no != 5:
				player_text_positions.append(Position(card_x, three_fifths_board))
				card_rects_on_board.append(
					Position(double_card_width, (player_text_positions[-1][1] - half_card_width))
				)

	return BoardDimensions(card_rects_on_board, player_text_positions)


@lru_cache
def board_height_helper(width: int, game_surf_height: int, window_margin: int, card_y: int) -> int:
	return min(width, (game_surf_height - window_margin - (card_y + 40)))


# noinspection PyAttributeOutsideInit
class BoardSurface(KnockSurfaceWithCards, TextBlitsMixin):
	__slots__ = 'player_text_positions', 'nonrelative_board_centre', 'standard_font'

	def __init__(self) -> None:
		self.card_list = game.played_cards
		self.card_fade_manager = OpacityFader(start_opacity=COVER_RECT_START_OPACITY, name='Board')
		self.card_update_queue = game.new_card_queues.played_cards
		super().__init__()   # calls surf_dimensions()
		SurfaceCoordinator.board_surf = self

	def initialise(self: B) -> B:
		self.standard_font = self.fonts[BoardSurfFonts.STANDARD_BOARD_FONT]
		return super().initialise()

	def surf_dimensions(self) -> None:
		game_surf_width, game_surf_height = self.game_surf.width, self.game_surf.height
		card_x, card_y = self.card_x, self.card_y

		self.width = width = game_surf_width // 2
		self.x = x = game_surf_height // 4
		self.y = y = self.window_margin
		self.height = height = board_height_helper(width, game_surf_height, y, card_y)

		w, h, x, y, ls = width, self.height, self.card_x, self.card_y, self.standard_font.linesize
		card_rects, self.player_text_positions = board_dimensions_helper(w, h, x, y, ls)
		self.add_rect_list(card_rects)

	def get_surf_and_pos(self) -> None:
		super().get_surf_and_pos()
		self.nonrelative_board_centre = (self.attrs.centre[0] + self.x, self.attrs.centre[1] + self.y)

	def update_card(self, card: Card, index: int) -> None:
		card.rect = self.rect_list[game.player_order[index]]

	def get_surf_blits(self) -> BlitsList:
		with game:
			whose_turn_player_index, trick_in_progress, round_leader_index = game.get_attributes((
				'whose_turn_playerindex', 'trick_in_progress', 'round_leader_index'
			))

		card_no, linesize, positions = len(self.card_list), self.standard_font.linesize, self.player_text_positions

		return super().get_surf_blits() + [self.get_text(t[0], t[1], center=t[2]) for t in Players.board_text(
			BoardTextArgs(whose_turn_player_index, trick_in_progress, card_no, linesize, round_leader_index),
			positions=positions
		)]
