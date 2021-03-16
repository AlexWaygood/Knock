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

from src.Misc_locals import GetDate
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

	def __init__(self, context: InputContext):
		self.LastClose = 0
		self.context = context
		self.Data = self.game.Scoreboard

	def save(self):
		if self.context.FireworksDisplay or not self.Data.Initialised:
			return None

		set_cursor(SYSTEM_CURSOR_WAIT)
		self.Data.scoreboard.to_csv(f'Knock_scoreboard_{GetDate()}.csv')

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
		fig, ax = plt_subplots()

		# hide axes
		ax.axis('off')
		ax.axis('tight')
		plt_rc('font', family='Times New Roman')

		fig.canvas.set_window_title('Knock scoreboard')
		fig.patch.set_facecolor('xkcd:scarlet')

		table = ax.table(
			cellText=self.Data.DisplayScoreboard.values,
			colLabels=self.Data.DisplayScoreboard.columns,
			loc='center',
			cellLoc='center',
			colColours=['none' for _ in self.Data.columns]
		)

		table.auto_set_font_size(False)

		for i, string in zip(range(2), ('B', 'BR')):
			table[0, i].visible_edges = string

		for (i, name), (j, string) in product(enumerate(self.Data.names), zip(range(2, 6), ('TBL', 'TB', 'TB', 'TBR'))):
			table[0, ((i * 4) + j)].visible_edges = string

		for i in range(self.Data.ColumnNo):
			table[1, i].set_facecolor(f'xkcd:burnt siena')

			for j in range(2):
				table[j, i].set_text_props(fontweight='bold')

		for i in range(2, (self.Data.DisplayScoreboard.index + 1)):
			for j in range(2):
				table[i, j].set_text_props(fontweight='bold')
				table[i, j].set_facecolor(f'xkcd:{"dark beige" if i % 2 else "pale brown"}')

			for j in range(2, self.Data.ColumnNo):
				if (j - 1) % 4:
					colour = "very light green" if i % 2 else "very light blue"
				else:
					try:
						Max = max(int(table[i, x].get_text().get_text()) for x in range(5, self.Data.ColumnNo, 4))
						assert int(table[i, j].get_text().get_text()) == Max
						colour = "periwinkle"
					except (ValueError, AssertionError):
						colour = 'baby blue'

				table[i, j].set_facecolor(f'xkcd:{colour}')

		ax.set_title('SCOREBOARD\n', fontname='Algerian', size=40)

		fig.tight_layout()

		manager = get_current_fig_manager()
		manager.window.showMaximized()
		manager.window.setWindowIcon(QIcon(self.IconFilePath))

		plt_show()
		self.LastClose = GetTicks()
