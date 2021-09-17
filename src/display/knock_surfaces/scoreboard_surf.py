from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Optional, Final

import src.static_constants as gc
from src.config import game

from src.display.abstract_surfaces import KnockSurface
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.faders import ColourFader

from src.players.players_client import ClientPlayer as Players

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList, Blittable
	from src.display import FontAndLinesize


SCOREBOARD_TITLE: Final = 'SCOREBOARD'


def trick_text(trick_no: int, card_no: int) -> str:
	if trick_no:
		return f'Trick {trick_no} of {card_no}'
	return 'Trick not in progress'


def round_text(round_no: int, start_card_no: int) -> str:
	return f'Round {round_no} of {start_card_no}'


def dimension_function_generator(player_no: int):
	@lru_cache
	def scoreboard_dimensions_helper(
			normal_font: FontAndLinesize,
			underlined_font: FontAndLinesize,
			games_played: int
	) -> tuple[float, float, Blittable, int]:

		normal_linesize = normal_font.linesize
		left_margin = int(normal_linesize * 1.75)
		max_points_text = max(normal_font.size(f'{player}: 188 points')[0] for player in Players)
		width = ((2 * left_margin) + max(max_points_text, underlined_font.size('Trick not in progress')[0]))
		multiplier = ((player_no * 2) + 7) if games_played else (player_no + 4)
		height = (normal_linesize * multiplier) + (2 * left_margin)
		title = (underlined_font.render(SCOREBOARD_TITLE), ((width // 2), int(normal_linesize * 1.5)))
		return width, height, title, left_margin
	return scoreboard_dimensions_helper


# noinspection PyAttributeOutsideInit,PyMissingConstructor
class ScoreboardSurface(KnockSurface, TextBlitsMixin):
	__slots__ = (
		'left_margin', 'title', 'fill_fade', 'normal_font', 'underlined_font', '_initialised', 'dimensions_helper_func'
	)

	def __init__(self, /) -> None:
		self._initialised = False
		self.dimensions_helper_func = dimension_function_generator(self.player_no)

	@property
	def initialised(self, /) -> bool:
		return self._initialised

	def real_init(self) -> None:
		super().__init__()    # calls surf_dimensions()
		self.fill_fade = ColourFader(gc.SCOREBOARD_FILL_COLOUR)
		self.get_surf()
		self._initialised = True
		self.activate()

	def get_surf(self, /) -> None:
		if self.initialised:
			super().get_surf()

	def initialise(self, /) -> Optional[ScoreboardSurface]:
		if self.initialised:
			super().initialise()
			self.normal_font = self.fonts[gc.NORMAL_SCOREBOARD_FONT]
			self.underlined_font = self.fonts[gc.UNDERLINED_SCOREBOARD_FONT]
			return self

	def fill(self, /) -> None:
		self.surf.fill(self.fill_fade.get_colour())

	def surf_dimensions(self, /) -> None:
		self.x = self.y = self.window_margin
		self.text_colour = self.colour_scheme[gc.TEXT_DEFAULT_FILL_COLOUR]
		self.width, self.height, self.title, self.left_margin = self.dimensions_helper_func(
			self.normal_font,
			self.underlined_font,
			game.games_played
		)

	def text_blits_helper(
			self,
			y: int,
			to_blit: BlitsList,
			attr: str
	) -> tuple[BlitsList, int]:

		normalfont = self.normal_font
		linesize = normalfont.linesize

		to_blit += [
			self.get_text(t[0], normalfont, **t[1])
			for t in Players.scoreboard_text(
				linesize=linesize,
				start_y=y,
				surf_width=self.width,
				left_margin=self.left_margin,
				attribute=attr)
		]

		return to_blit, (y + (linesize * self.player_no))

	def get_surf_blits(self, /) -> BlitsList:
		trick_no, card_no, round_no, start_card_no, games_played = game.get_attributes((
			'trick_number', 'card_number', 'round_number', 'start_card_no', 'games_played'
		))

		scoreboard_blits = [self.title]
		normal_font, linesize = self.normal_font, self.normal_font.linesize
		y = self.title[1] + linesize
		scoreboard_blits, y = self.text_blits_helper(y, scoreboard_blits, gc.SCOREBOARD_TEXT_KEY_1)
		y += linesize * 2

		message1 = self.get_text(round_text(round_no, start_card_no), normal_font, center=(self.attrs.centre[0], y))
		message2 = self.get_text(trick_text(card_no, trick_no), normal_font, center=(self.attrs.centre[0], (y + linesize)))
		scoreboard_blits += [message1, message2]

		if games_played:
			y += linesize * 3
			scoreboard_blits.append(self.get_text('-----', normal_font, center=(self.attrs.centre[0], y)))
			y += linesize
			scoreboard_blits, y = self.text_blits_helper(y, scoreboard_blits, gc.SCOREBOARD_TEXT_KEY_2)

		return scoreboard_blits
