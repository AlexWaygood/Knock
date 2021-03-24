from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING
from src.display.abstract_surfaces.knock_surface import KnockSurface
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.faders import ColourFader
from src.players.players_client import ClientPlayer as Player

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList


def DimensionFunctionGenerator(PlayerNo):
	@lru_cache
	def ScoreboardDimensionsHelper(NormalFont, UnderlinedFont, GamesPlayed):
		NormalLineSize = NormalFont.linesize
		LeftMargin = int(NormalLineSize * 1.75)
		MaxPointsText = max(NormalFont.size(f'{player}: 88 points')[0] for player in Player.iter())
		Width = ((2 * LeftMargin) + max(MaxPointsText, UnderlinedFont.size('Trick not in progress')[0]))
		Multiplier = ((PlayerNo * 2) + 7) if GamesPlayed else (PlayerNo + 4)
		Height = (NormalLineSize * Multiplier) + (2 * LeftMargin)
		title = (UnderlinedFont.render('SCOREBOARD'), ((Width // 2), int(NormalLineSize * 1.5)))
		return Width, Height, title, LeftMargin
	return ScoreboardDimensionsHelper


# noinspection PyAttributeOutsideInit,PyMissingConstructor
class Scoreboard(KnockSurface, TextBlitsMixin):
	__slots__ = 'LeftMargin', 'title', 'FillFade', 'NormalFont', 'UnderlinedFont', 'Initialised', 'DimensionsHelperFunc'

	def __init__(self):
		self.Initialised = False
		self.DimensionsHelperFunc = DimensionFunctionGenerator(self.PlayerNo)

	def RealInit(self):
		super().__init__()    # calls SurfDimensions()
		self.FillFade = ColourFader('Scoreboard')
		self.GetSurf()
		self.Initialised = True
		self.OnScreen = True

	def GetSurf(self):
		if self.Initialised:
			super().GetSurf()

	def Initialise(self):
		if self.Initialised:
			super().Initialise()
			self.NormalFont = self.Fonts['NormalScoreboardFont']
			self.UnderlinedFont = self.Fonts['UnderlinedScoreboardFont']
			return self

	def fill(self):
		self.surf.fill(self.FillFade.GetColour())

	def SurfDimensions(self):
		self.x = self.y = self.WindowMargin
		self.TextColour = self.ColourScheme.TextDefault
		self.Width, self.Height, self.title, self.LeftMargin = self.DimensionsHelperFunc(
			self.NormalFont,
			self.UnderlinedFont,
			self.game.GamesPlayed
		)

	def TextBlitsHelper(
			self,
			y: int,
			ScoreboardBlits: BlitsList,
			attr: str
	):
		ScoreboardBlits += [
			self.GetText(tup[0], self.NormalFont, **tup[1])
			for tup in Player.ScoreboardText(self.NormalFont.linesize, y, self.Width, self.LeftMargin, attr)
		]

		return ScoreboardBlits, (y + (self.NormalFont.linesize * self.PlayerNo))

	def GetSurfBlits(self):
		TrickNo, CardNo, RoundNo, StartCardNo, GamesPlayed = self.game.GetAttributes((
			'TrickNumber', 'CardNumber', 'RoundNumber', 'StartCardNumber', 'GamesPlayed'
		))

		ScoreboardBlits = [self.title]
		NormalFont, NormalLineSize = self.NormalFont, self.NormalFont.linesize
		y = self.title[1] + NormalLineSize
		ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, 'point')
		y += NormalLineSize * 2

		Message1 = self.GetText(f'Round {RoundNo} of {StartCardNo}', NormalFont, center=(self.attrs.centre[0], y))
		TrickText = f'Trick {TrickNo} of {CardNo}' if TrickNo else 'Trick not in progress'
		Message2 = self.GetText(TrickText, NormalFont, center=(self.attrs.centre[0], (y + NormalLineSize)))
		ScoreboardBlits += [Message1, Message2]

		if GamesPlayed:
			y += NormalLineSize * 3
			ScoreboardBlits.append(self.GetText('-----', NormalFont, center=(self.attrs.centre[0], y)))
			y += NormalLineSize
			ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, 'game')

		return ScoreboardBlits
