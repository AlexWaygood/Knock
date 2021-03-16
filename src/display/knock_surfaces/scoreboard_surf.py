from __future__ import annotations

from typing import TYPE_CHECKING
from src.display.abstract_surfaces.knock_surface import KnockSurface
from src.display.abstract_surfaces.text_rendering import TextBlitsMixin
from src.display.faders import ColourFader

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList, ScoreboardGenerator


# noinspection PyAttributeOutsideInit
class Scoreboard(KnockSurface, TextBlitsMixin):
	__slots__ = 'LeftMargin', 'title', 'FillFade', 'NormalFont', 'UnderlinedFont'

	def __init__(self):
		super().__init__()    # calls SurfDimensions()
		self.FillFade = ColourFader()

	def Initialise(self):
		super().Initialise()
		self.NormalFont = self.Fonts['NormalScoreboardFont']
		self.UnderlinedFont = self.Fonts['UnderlinedScoreboardFont']

	def fill(self):
		if c := self.FillFade.GetColour():
			self.colour = c
		self.attrs.surf.fill(self.colour)

	def SurfDimensions(self):
		self.x = self.WindowMargin
		self.y = self.WindowMargin
		NormalLineSize = self.NormalFont.linesize
		self.LeftMargin = int(NormalLineSize * 1.75)
		self.players = self.game.gameplayers
		self.PlayerNo = self.players.PlayerNo

		MaxPointsText = max(self.NormalFont.size(f'{str(player)}: 88 points')[0] for player in self.players)
		self.TextColour = (0, 0, 0)

		self.SurfWidth = (
				(2 * self.LeftMargin)
				+ max(MaxPointsText, self.UnderlinedFont.size('Trick not in progress')[0])
		)

		Multiplier = ((self.PlayerNo * 2) + 7) if self.game.GamesPlayed else (self.PlayerNo + 4)
		self.SurfHeight = (NormalLineSize * Multiplier) + (2 * self.LeftMargin)
		self.title = (self.UnderlinedFont.render('SCOREBOARD'), (self.attrs.centre[0], int(NormalLineSize * 1.5)))

	def TextBlitsHelper(
			self,
			y: int,
			ScoreboardBlits: BlitsList,
			Gen: ScoreboardGenerator):

		for Message in Gen:
			args = ({'topleft': (self.LeftMargin, y)}, {'topright': ((self.SurfWidth - self.LeftMargin), y)})
			ScoreboardBlits += [self.GetText(Message[i], self.NormalFont, **arg) for i, arg in enumerate(args)]
			y += self.NormalFont.linesize

		return ScoreboardBlits, y

	def ScoreboardText(self):
		for player in self.players.HighestScoreFirst():
			yield f'{player}:', f'{player.Points} point{"s" if player.Points != 1 else ""}'

	def ScoreboardText2(self):
		for player in self.players.MostGamesWonFirst():
			yield f'{player}:', f'{player.GamesWon} game{"s" if player.GamesWon != 1 else ""}'

	def GetSurfBlits(self):
		TrickNo, CardNo, RoundNo, StartCardNo, GamesPlayed = self.game.GetAttributes((
			'TrickNumber', 'CardNumber', 'RoundNumber', 'StartCardNumber', 'GamesPlayed'
		))

		ScoreboardBlits = [self.title]
		NormalFont, NormalLineSize = self.NormalFont, self.NormalFont.linesize
		y = self.title[1] + NormalLineSize
		ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, self.ScoreboardText())
		y += NormalLineSize * 2

		Message1 = self.GetText(f'Round {RoundNo} of {StartCardNo}', NormalFont, center=(self.attrs.centre[0], y))
		TrickText = f'Trick {TrickNo} of {CardNo}' if TrickNo else 'Trick not in progress'
		Message2 = self.GetText(TrickText, NormalFont, center=(self.attrs.centre[0], (y + NormalLineSize)))
		ScoreboardBlits += [Message1, Message2]

		if GamesPlayed:
			y += NormalLineSize * 3
			ScoreboardBlits.append(self.GetText('-----', NormalFont, center=(self.attrs.centre[0], y)))
			y += NormalLineSize
			ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, self.ScoreboardText2())

		return ScoreboardBlits
