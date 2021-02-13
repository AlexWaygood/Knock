"""Several classes that are themselves wrappers around pygame classes, to make the client script cleaner"""

from collections import UserList
from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect
import pygame.display as display


def RestartDisplay():
	display.quit()
	display.init()


class SurfaceAndPosition(object):
	"""Class for holding data about various surfaces that will be used frequently in the game"""

	__slots__ = 'surf', 'pos', 'surfandpos', 'RectList', 'midpoint', 'CoverRects', 'Dimensions', 'CardFadeInProgress',\
	            'name'

	CardDimensions = None
	DefaultFillColour = None

	def __init__(self, name, SurfaceDimensions=None, position=None, RectList=None,
	             Dimensions=None, OpacityRequired=False, FillColour=None,
	             CoverRectOpacity=0):

		self.name = name
		FillColour = FillColour if FillColour else self.DefaultFillColour

		if position:
			self.pos = position

		if SurfaceDimensions:
			self.AddSurf(SurfaceDimensions, position, OpacityRequired, FillColour)

		self.AddRectList(RectList, CoverRectOpacity, FillColour)

		if Dimensions:
			self.midpoint = Dimensions[0] // 2

	def AddSurf(self, SurfaceDimensions, pos=None, OpacityRequired=False, FillColour=None):
		self.Dimensions = SurfaceDimensions
		self.surf = Surface(SurfaceDimensions)

		if OpacityRequired:
			self.surf = self.surf.convert_alpha()

		self.surf.fill(FillColour)

		if pos:
			self.pos = pos

		self.surfandpos = (self.surf, self.pos)

	def ShiftPos(self, PosIndex, Shift):
		self.pos[PosIndex] += Shift
		self.surfandpos = (self.surf, self.pos)

	def ResetPos(self):
		self.pos = [0, 0]
		self.surfandpos = (self.surf, self.pos)

	def AddRectList(self, Positions, CoverRectOpacity, Colour):
		self.RectList = [Rect(*Position, *self.CardDimensions) for Position in Positions] if Positions else []
		args = (self.CardDimensions, Colour, CoverRectOpacity)
		self.CoverRects = CoverRectList([CoverRect(rect, *args) for rect in self.RectList])

	@classmethod
	def AddDefaults(cls, CardDimensions, DefaultFill):
		cls.CardDimensions = CardDimensions
		cls.DefaultFillColour = DefaultFill

	def ClearRectList(self):
		self.RectList.clear()
		self.CoverRects.clear()

	def SetCoverRectOpacity(self, *args):
		self.CoverRects.SetOpacity(*args)

	def fill(self, *args):
		self.surf.fill(*args)
		self.CoverRects.fill(*args)

	def blit(self, *args):
		self.surf.blit(*args)

	def blits(self, *args):
		self.surf.blits(*args)

	def __repr__(self):
		return self.name


class CoverRect(object):
	__slots__ = 'surf', 'rect', 'surfandrect'

	def __init__(self, rect, CardDimensions, colour, Opacity):
		self.surf = Surface(CardDimensions)
		self.rect = rect
		self.surf.fill(colour)
		self.surf.set_alpha(Opacity)
		self.surfandrect = (self.surf, self.rect)


class CoverRectList(UserList):
	def __init__(self, data):
		super().__init__()
		self.data = data
		self.coverrects = self.data

	def SetOpacity(self, *args):
		for cv in self.coverrects:
			cv.surf.set_alpha(*args)

	def fill(self, *args):
		for cv in self.coverrects:
			cv.surf.fill(*args)


class FontAndLinesize(object):
	"""Class for holding data about various fonts that will be used frequently in the game"""

	__slots__ = 'font', 'linesize'

	def __init__(self, font):
		self.font = font
		self.linesize = font.get_linesize()

	def render(self, *args):
		return self.font.render(*args)

	def size(self, text):
		return self.font.size(text)
