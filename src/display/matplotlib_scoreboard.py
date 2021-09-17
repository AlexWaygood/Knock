from __future__ import annotations

import matplotlib.pyplot as plt

from os import path
from typing import TYPE_CHECKING, Final
from itertools import product
from PyQt5.QtGui import QIcon

from src.display.surface_coordinator import SurfaceCoordinator

# noinspection PyUnresolvedReferences
from src import pre_pygame_import, get_date
from src.config import game, client
from pygame.locals import SYSTEM_CURSOR_WAIT
from pygame.mouse import set_cursor
from pygame.time import get_ticks

if TYPE_CHECKING:
	from src.display.input_context import GameInputContextManager


SCOREBOARD_EVENT_FREQUENCY: Final = 500
ICON_FILE_PATH: Final = path.join('..', '..', 'Images', 'Cards', 'PyinstallerIcon.ico')
FILE_SAVE_PATH: Final = f'Knock_scoreboard_{get_date()}.csv'

WINDOW_CAPTION: Final = 'Knock scoreboard'
TITLE: Final = 'SCOREBOARD'

TITLE_FONT: Final = 'Algerian'
TITLE_SIZE: Final = 40
STANDARD_FONT: Final = 'Times New Roman'

BACKGROUND_COLOUR: Final = 'xkcd:scarlet'
HEADER_COLOUR: Final = 'xkcd:burnt siena'

FIRST_TWO_COLUMNS_COLOUR_1: Final = 'xkcd:dark beige'
FIRST_TWO_COLUMNS_COLOUR_2: Final = 'xkcd:pale brown'

STANDARD_CELL_COLOUR_1: Final = 'xkcd:very light green'
STANDARD_CELL_COLOUR_2: Final = 'xkcd:very light blue'

CUMULATIVE_SCORE_COLUMN_COLOUR_1: Final = 'xkcd:periwinkle'
CUMULATIVE_SCORE_COLUMN_COLOUR_2: Final = 'xkcd:baby blue'


# noinspection PyAttributeOutsideInit
class InteractiveScoreboard(SurfaceCoordinator):
	__slots__ = 'last_close', 'context', 'data'

	def __init__(self, /, *, context: GameInputContextManager) -> None:
		self.last_close = 0
		self.context = context
		self.data = game.scoreboard_data

	def save(self, /) -> None:
		if not self.context.fireworks_display and self.data.initialised:
			set_cursor(SYSTEM_CURSOR_WAIT)
			self.data.scoreboard_data.to_csv(FILE_SAVE_PATH)

	def show(self, /) -> None:
		condition = (
				client.connection_broken
				or self.context.fireworks_display
				or (not self.data.initialised)
				or (get_ticks() < self.last_close + SCOREBOARD_EVENT_FREQUENCY)
		)

		if condition:
			return

		set_cursor(SYSTEM_CURSOR_WAIT)

		# Basically equivalent to matplotlib.init()
		fig, ax = plt.subplots()

		# hide axes
		ax.axis('off')
		ax.axis('tight')
		plt.rc('font', family=STANDARD_FONT)

		# Set the window caption and the background colour for the window.
		fig.canvas.set_window_title(WINDOW_CAPTION)
		fig.patch.set_facecolor(BACKGROUND_COLOUR)

		# Tell matplotlib what data to use
		table = ax.table(
			cellText=self.data.display_scoreboard.values,
			colLabels=self.data.display_scoreboard.column_names,
			loc='center',
			cellLoc='center',
			colColours=['none' for _ in self.data.column_names]
		)

		table.auto_set_font_size(False)

		# Set the cell borders for the first row only (the row with just the player_names).
		for i, string in zip(range(2), ('B', 'BR')):
			table[0, i].visible_edges = string

		# Set the cell borders for all the other rows.
		for (i, name), (j, string) in product(
				enumerate(self.data.player_names),
				zip(range(2, 6), ('TBL', 'TB', 'TB', 'TBR'))
		):
			table[0, ((i * 4) + j)].visible_edges = string

		# Set the text-colour and formatting for the header row(s).
		for i in range(self.data.column_no):
			table[1, i].set_facecolor(HEADER_COLOUR)

			for j in range(2):
				table[j, i].set_text_props(fontweight='bold')

		for i in range(2, (self.data.display_scoreboard.index + 1)):
			# Set the colour for the first two column_names (alternating every other row).
			for j in range(2):
				table[i, j].set_text_props(fontweight='bold')
				table[i, j].set_facecolor(FIRST_TWO_COLUMNS_COLOUR_1 if i % 2 else FIRST_TWO_COLUMNS_COLOUR_2)

			# Set the colours for the other column_names
			# For all column_names except the cumulative score, it alternates row by row.
			# For the cumulative score, the person who got the most points that round is highlighted with a different colour.
			for j in range(2, self.data.column_no):
				if (j - 1) % 4:
					colour = STANDARD_CELL_COLOUR_1 if i % 2 else STANDARD_CELL_COLOUR_2
				else:
					try:
						max_n = max(int(table[i, x].get_text().get_text()) for x in range(5, self.data.column_no, 4))
						assert int(table[i, j].get_text().get_text()) == max_n
						colour = STANDARD_CELL_COLOUR_1
					except (ValueError, AssertionError):
						colour = STANDARD_CELL_COLOUR_2

				table[i, j].set_facecolor(colour)

		# Set the title of the scoreboard
		ax.set_title(f'{TITLE}\n', fontname=TITLE_FONT, size=TITLE_SIZE)

		# Sort the formatting, make sure it will launch full screen, set the window icon.
		fig.tight_layout()
		manager = plt.get_current_fig_manager()
		manager.window.showMaximized()
		manager.window.setWindowIcon(QIcon(ICON_FILE_PATH))

		# Launch the window.
		plt.show()

		# This will only be reached after the window is closed.
		# Record what time the window is closed so that it doesn't get immediately relaunched by duplicate pygame events.
		self.last_close = get_ticks()
