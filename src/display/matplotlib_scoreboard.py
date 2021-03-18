from __future__ import annotations

from matplotlib.pyplot import (
	get_current_fig_manager,
	subplots as plt_subplots,
	rc as plt_rc,
	show as plt_show
)

from typing import TYPE_CHECKING
from itertools import product
from PyQt5.QtGui import QIcon

from src.misc import GetDate
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator

from os import path, environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.locals import SYSTEM_CURSOR_WAIT
from pygame.mouse import set_cursor
from pygame.time import get_ticks as GetTicks

if TYPE_CHECKING:
	from src.display.input_context import InputContext


# noinspection PyAttributeOutsideInit
class InteractiveScoreboard(SurfaceCoordinator):
	__slots__ = 'LastClose', 'context', 'Data'

	IconFilePath = path.join('..', '..', 'Images', 'Cards', 'PyinstallerIcon.ico')
	FileSavePath = f'Knock_scoreboard_{GetDate()}.csv'

	WindowCaption = 'Knock scoreboard'
	Title = 'SCOREBOARD'

	TitleFont = 'Algerian'
	TitleSize = 40
	StandardFont = 'Times New Roman'

	BackgroundColour = 'xkcd:scarlet'
	HeaderColour = 'xkcd:burnt siena'

	FirstTwoColumnsColour1 = 'xkcd:dark beige'
	FirsTwoColumnsColour2 = 'xkcd:pale brown'

	StandardCellColour1 = 'xkcd:very light green'
	StandardCellColour2 = 'xkcd:very light blue'

	CumulativeScoreColumnColour1 = 'xkcd:periwinkle'
	CumulativeScoreColumnColour2 = 'xkcd:baby blue'

	def __init__(self, context: InputContext):
		self.LastClose = 0
		self.context = context
		self.Data = self.game.Scoreboard

	def save(self):
		if self.context.FireworksDisplay or not self.Data.Initialised:
			return None

		set_cursor(SYSTEM_CURSOR_WAIT)
		self.Data.scoreboard.to_csv(self.FileSavePath)

	def show(self):
		Condition = (
				self.client.ConnectionBroken
				or self.context.FireworksDisplay
				or (not self.Data.Initialised)
				or (GetTicks() < self.LastClose + 500)
		)

		if Condition:
			return None

		set_cursor(SYSTEM_CURSOR_WAIT)

		# Basically equivalent to matplotlib.init()
		fig, ax = plt_subplots()

		# hide axes
		ax.axis('off')
		ax.axis('tight')
		plt_rc('font', family=self.StandardFont)

		# Set the window caption and the background colour for the window.
		fig.canvas.set_window_title(self.WindowCaption)
		fig.patch.set_facecolor(self.BackgroundColour)

		# Tell matplotlib what data to use
		table = ax.table(
			cellText=self.Data.DisplayScoreboard.values,
			colLabels=self.Data.DisplayScoreboard.columns,
			loc='center',
			cellLoc='center',
			colColours=['none' for _ in self.Data.columns]
		)

		table.auto_set_font_size(False)

		# Set the cell borders for the first row only (the row with just the names).
		for i, string in zip(range(2), ('B', 'BR')):
			table[0, i].visible_edges = string

		# Set the cell borders for all the other rows.
		for (i, name), (j, string) in product(enumerate(self.Data.names), zip(range(2, 6), ('TBL', 'TB', 'TB', 'TBR'))):
			table[0, ((i * 4) + j)].visible_edges = string

		# Set the text-colour and formatting for the header row(s).
		for i in range(self.Data.ColumnNo):
			table[1, i].set_facecolor(self.HeaderColour)

			for j in range(2):
				table[j, i].set_text_props(fontweight='bold')

		for i in range(2, (self.Data.DisplayScoreboard.index + 1)):
			# Set the colour for the first two columns (alternating every other row).
			for j in range(2):
				table[i, j].set_text_props(fontweight='bold')
				table[i, j].set_facecolor(self.FirstTwoColumnsColour1 if i % 2 else self.FirsTwoColumnsColour2)

			# Set the colours for the other columns
			# For all columns except the cumulative score, it alternates row by row.
			# For the cumulative score, the person who got the most points that round is highlighted with a different colour.
			for j in range(2, self.Data.ColumnNo):
				if (j - 1) % 4:
					colour = self.StandardCellColour1 if i % 2 else self.StandardCellColour2
				else:
					try:
						Max = max(int(table[i, x].get_text().get_text()) for x in range(5, self.Data.ColumnNo, 4))
						assert int(table[i, j].get_text().get_text()) == Max
						colour = self.CumulativeScoreColumnColour1
					except (ValueError, AssertionError):
						colour = self.CumulativeScoreColumnColour2

				table[i, j].set_facecolor(colour)

		# Set the title of the scoreboard
		ax.set_title(f'{self.Title}\n', fontname=self.TitleFont, size=self.TitleSize)

		# Sort the formatting, make sure it will launch full screen, set the window icon.
		fig.tight_layout()
		manager = get_current_fig_manager()
		manager.window.showMaximized()
		manager.window.setWindowIcon(QIcon(self.IconFilePath))

		# Launch the window.
		plt_show()

		# This will only be reached after the window is closed.
		# Record what time the window is closed so that it doesn't get immediately relaunched by duplicate pygame events.
		self.LastClose = GetTicks()
