import matplotlib.pyplot as plt
import pandas as pd
from itertools import product
from PyQt5 import QtGui

from os import path, environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import SYSTEM_CURSOR_WAIT
from pygame.mouse import set_cursor
from pygame.time import get_ticks as GetTicks


class InteractiveScoreboard:
	__slots__ = 'LastClose', 'PlayerNoTimes4', 'ColumnNo', 'names', 'columns', 'StartNo', 'scoreboard', \
	            'DisplayScoreboard', 'game'

	def __init__(self, game):
		self.game = game
		self.LastClose = 0
		self.PlayerNoTimes4 = self.game.PlayerNumber * 4
		self.ColumnNo = self.PlayerNoTimes4 + 2
		self.names = [f'{player}' for player in self.game.gameplayers]
		self.columns = ['', ''] + sum((['', name, '', ''] for name in self.names), start=[])
		self.StartNo = self.game.StartCardNumber

		self.scoreboard = pd.DataFrame(
			[['Round', 'Cards'] + sum((['Bid', 'Won', 'Points', 'Score'] for _ in self.names), start=[])],
			columns=self.columns
		)

		self.DisplayScoreboard = self.FillBlanks(0)

	def UpdateScores(self):
		with self.game:
			RoundNumber, CardNumber, players = self.game.GetAttributes((
				'RoundNumber', 'CardNumberThisRound', 'gameplayers'
			))

		NewRow = pd.DataFrame(
			[[RoundNumber, CardNumber] + sum((player.Scoreboard for player in players), start=[])],
			columns=self.columns
		)

		self.scoreboard = pd.concat(self.scoreboard, NewRow, ignore_index=True)
		self.DisplayScoreboard = self.FillBlanks(RoundNumber)

	def FillBlanks(self, RoundNumber: int):
		Blanks = pd.DataFrame([
			([x, y] + [None for _ in range(self.PlayerNoTimes4)])

			for x, y in zip(
				range((RoundNumber + 1), (self.StartNo + 1)),
				range((self.StartNo - RoundNumber), 0, -1)
			)
		])

		return pd.concat((self.scoreboard, Blanks), ignore_index=True)

	def show(self):
		if GetTicks() < self.LastClose + 500:
			return None

		set_cursor(SYSTEM_CURSOR_WAIT)
		fig, ax = plt.subplots()

		# hide axes
		ax.axis('off')
		ax.axis('tight')
		plt.rc('font', family='Times New Roman')

		fig.canvas.set_window_title('Knock scoreboard')
		fig.patch.set_facecolor('xkcd:scarlet')

		table = ax.table(
			cellText=self.DisplayScoreboard.values,
			colLabels=self.DisplayScoreboard.columns,
			loc='center',
			cellLoc='center',
			colColours=['none' for _ in self.columns]
		)

		table.auto_set_font_size(False)

		for i, string in zip(range(2), ('B', 'BR')):
			table[0, i].visible_edges = string

		for (i, name), (j, string) in product(enumerate(self.names), zip(range(2, 6), ('TBL', 'TB', 'TB', 'TBR'))):
			table[0, ((i * 4) + j)].visible_edges = string

		for i in range(self.ColumnNo):
			table[1, i].set_facecolor(f'xkcd:burnt siena')

			for j in range(2):
				table[j, i].set_text_props(fontweight='bold')

		for i in range(2, (self.DisplayScoreboard.index + 1)):
			for j in range(2):
				table[i, j].set_text_props(fontweight='bold')
				table[i, j].set_facecolor(f'xkcd:{"dark beige" if i % 2 else "pale brown"}')

			for j in range(2, self.ColumnNo):
				if (j - 1) % 4:
					colour = "very light green" if i % 2 else "very light blue"
				else:
					try:
						Max = max(int(table[i, x].get_text().get_text()) for x in range(5, self.ColumnNo, 4))
						assert int(table[i, j].get_text().get_text()) == Max
						colour = "periwinkle"
					except (ValueError, AssertionError):
						colour = 'baby blue'

				table[i, j].set_facecolor(f'xkcd:{colour}')

		ax.set_title('SCOREBOARD\n', fontname='Algerian', size=40)

		fig.tight_layout()

		manager = plt.get_current_fig_manager()
		manager.window.showMaximized()
		manager.window.setWindowIcon(QtGui.QIcon(path.join('..', '..', 'Images', 'Cards', 'PyinstallerIcon.ico')))

		plt.show()
		self.LastClose = GetTicks()
