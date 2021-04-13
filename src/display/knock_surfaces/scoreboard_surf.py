from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING
from src.display.abstract_surfaces.knock_surface import KnockSurface
from src.display.abstract_text_rendering import TextBlitsMixin
from src.display.faders import ColourFader
from src.players.players_client import ClientPlayer as Player

if TYPE_CHECKING:
	from src.special_knock_types import BlitsList
	from src.display.abstract_text_rendering import FontAndLinesize


NORMAL_FONT = 'NormalScoreboardFont'
UNDERLINED_FONT = 'UnderlinedScoreboardFont'
SCOREBOARD_TITLE = 'SCOREBOARD'


def TrickText(TrickNo: int, CardNo: int):
	if TrickNo:
		return f'Trick {TrickNo} of {CardNo}'
	return 'Trick not in progress'


def RoundText(RoundNo: int, StartCardNo: int):
	return f'Round {RoundNo} of {StartCardNo}'


def DimensionFunctionGenerator(PlayerNo: int):
	@lru_cache
	def ScoreboardDimensionsHelper(
			NormalFont: FontAndLinesize,
			UnderlinedFont: FontAndLinesize,
			GamesPlayed: int
	):
		NormalLineSize = NormalFont.linesize
		LeftMargin = int(NormalLineSize * 1.75)
		MaxPointsText = max(NormalFont.size(f'{player}: 188 points')[0] for player in Player.iter())
		Width = ((2 * LeftMargin) + max(MaxPointsText, UnderlinedFont.size('Trick not in progress')[0]))
		Multiplier = ((PlayerNo * 2) + 7) if GamesPlayed else (PlayerNo + 4)
		Height = (NormalLineSize * Multiplier) + (2 * LeftMargin)
		title = (UnderlinedFont.render(SCOREBOARD_TITLE), ((Width // 2), int(NormalLineSize * 1.5)))
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
			self.NormalFont = self.Fonts[NORMAL_FONT]
			self.UnderlinedFont = self.Fonts[UNDERLINED_FONT]
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
			ToBlit: BlitsList,
			attr: str
	):
		font, linesize, width, Margin = self.NormalFont, self.NormalFont.linesize, self.Width, self.LeftMargin
		ToBlit += [self.GetText(t[0], font, **t[1]) for t in Player.ScoreboardText(linesize, y, width, Margin, attr)]
		return ToBlit, (y + (linesize * self.PlayerNo))

	def GetSurfBlits(self):
		TrickNo, CardNo, RoundNo, StartCardNo, GamesPlayed = self.game.GetAttributes((
			'TrickNumber', 'CardNumber', 'RoundNumber', 'StartCardNumber', 'GamesPlayed'
		))

		ScoreboardBlits = [self.title]
		NormalFont, LineSize = self.NormalFont, self.NormalFont.linesize
		y = self.title[1] + LineSize
		ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, 'point')
		y += LineSize * 2

		Message1 = self.GetText(RoundText(RoundNo, StartCardNo), NormalFont, center=(self.attrs.centre[0], y))
		Message2 = self.GetText(TrickText(CardNo, TrickNo), NormalFont, center=(self.attrs.centre[0], (y + LineSize)))
		ScoreboardBlits += [Message1, Message2]

		if GamesPlayed:
			y += LineSize * 3
			ScoreboardBlits.append(self.GetText('-----', NormalFont, center=(self.attrs.centre[0], y)))
			y += LineSize
			ScoreboardBlits, y = self.TextBlitsHelper(y, ScoreboardBlits, 'game')

		return ScoreboardBlits
