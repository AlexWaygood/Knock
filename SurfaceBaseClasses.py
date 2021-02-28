from functools import lru_cache, singledispatchmethod
import pygame as pg
from typing import Sequence


class CoverRect(object):
	__slots__ = 'surf', 'rect', 'surfandpos'

	def __init__(self, rect, CardDimensions, Opacity):
		self.surf = pg.Surface(CardDimensions)
		self.rect = rect
		self.surf.set_alpha(Opacity)
		self.surfandpos = (self.surf, self.rect)


class Fader(object):
	def __init__(self):
		self.Fade = False
		self.StartTime = 0
		self.EndTime = 0
		self.Colour1 = tuple()
		self.Colour2 = tuple()
		self.TimeToTake = 0

	@singledispatchmethod
	def ScheduleFade(self, colour1, colour2, TimeToTake):
		self.StartTime = pg.time.get_ticks()
		self.Colour1 = colour1
		self.Colour2 = colour2
		self.TimeToTake = TimeToTake
		self.EndTime = pg.time.get_ticks() + TimeToTake

	@ScheduleFade.register
	def ScheduleFade(self, colour1: int, colour2: int, TimeToTake):
		self.ScheduleFade([colour1], [colour2], TimeToTake)

	def GetColour(self, OpacityFade=False):
		if (Time := pg.time.get_ticks()) > self.EndTime:
			self.Fade = False
			return self.Colour2[1] if OpacityFade else self.Colour2

		Elapsed = Time - self.StartTime

		ColourStep = [
			(((self.Colour2[i] - self.Colour1[i]) / self.TimeToTake) * Elapsed)
			for i, in range(len(self.Colour1))
		]


	def __bool__(self):
		return self.Fade


# noinspection PyAttributeOutsideInit
class BaseKnockSurface(object):
	__slots__ = 'SurfWidth', 'SurfHeight', 'x', 'y', 'surf', 'colour', 'rect', 'topleft', 'Dimensions', 'centre', \
	            'surfandpos', 'FadeInProgress'

	def __init__(self, FillColour):
		self.FadeInProgress = False
		self.colour = FillColour

	def SurfAndPos(self):
		self.surf = pg.Surface((self.SurfWidth, self.SurfHeight))
		self.fill()
		self.rect = pg.Rect(self.x, self.y, self.SurfWidth, self.SurfHeight)
		self.topleft = (self.x, self.y)
		self.Dimensions = (self.SurfWidth, self.SurfHeight)
		self.centre = ((self.SurfWidth / 2), (self.SurfHeight / 2))
		self.surfandpos = (self.surf, self.rect)

	def fill(self):
		self.surf.fill(self.colour)


class KnockSurface(BaseKnockSurface):
	__slots__ = 'colour', 'Iteration', 'OnScreen'

	def __init__(self, FillColour, *args, **kwargs):
		super().__init__(FillColour)
		self.Iteration = 0
		self.OnScreen = False
		self.InitialiseSurf(FillColour, *args, **kwargs)

	def SurfDimensions(self, *args, **kwargs):
		pass

	# This method is used from __init__ and from NewWindowSize
	def InitialiseSurf(self, *args, **kwargs):
		self.SurfDimensions(*args, **kwargs)
		self.SurfAndPos()

	def GetSurfBlits(self, *args, **kwargs):
		return []

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		return exc_val == "Not currently on the screen"

	def Update(self, ServerIteration, ForceUpdate=False, *args, **kwargs):
		if not self.OnScreen:
			raise Exception("Not currently on the screen")

		if not (ServerIteration > self.Iteration or self.FadeInProgress or ForceUpdate):
			return None

		self.Iteration = ServerIteration
		self.fill()
		self.surf.blits(self.GetSurfBlits(*args, **kwargs), False)
		return True


# noinspection PyAttributeOutsideInit
class KnockSurfaceWithCards(KnockSurface):
	__slots__ = 'CoverRectOpacity', 'GameSurfWidth', 'GameSurfHeight', 'RectList', 'CoverRects'

	def __init__(self, FillColour, *args, **kwargs):
		super().__init__(FillColour, *args, **kwargs)
		self.CoverRectOpacity = 255

	def AddCardRects(self, CardX, CardY, CardPositions: Sequence):
		self.RectList = [pg.Rect(p[0], p[1], CardX, CardY) for p in CardPositions]
		self.CoverRects = [CoverRect(rect, (CardX, CardY), self.CoverRectOpacity) for rect in self.RectList]

	def ClearRectList(self):
		self.RectList.clear()
		self.CoverRects.clear()

	def SetCoverRectOpacity(self, opacity):
		self.CoverRectOpacity = opacity

		for cv in self.CoverRects:
			cv.surf.set_alpha(opacity)

	def fill(self):
		self.surf.fill(self.colour)

		for cv in self.CoverRects:
			cv.surf.fill(self.colour)

	def UpdateCardOnArrival(self, index, card, *args, **kwargs):
		pass

	def GetSurfBlits(self, cards, *args, **kwargs):
		for i, card in enumerate(cards):
			self.UpdateCardOnArrival(i, card, *args, **kwargs)

		L = [card.surfandpos for card in cards]

		if self.FadeInProgress and cards:
			L += [cv.surfandpos for cv in self.CoverRects]

		return L

	def Update(self, ServerIteration, ForceUpdate=False, cards: Sequence = tuple(), *args, **kwargs):
		return super().Update(ServerIteration, ForceUpdate, cards, *args, **kwargs)


class TextBlitsMixin(object):
	__slots__ = 'TextColour'

	def __init__(self):
		self.TextColour = (0, 0, 0)

	@lru_cache
	def GetText(self, text, font, **kwargs):
		text = font.render(text, False, self.TextColour)
		return text, text.get_rect(**kwargs)


class FixedTextBlitsMixin(TextBlitsMixin):
	__slots__ = 'Text'

	def GetPresetText(self, font, center):
		return [((None, center) if not self.Text else self.GetText(self.Text, font, center=center))]
