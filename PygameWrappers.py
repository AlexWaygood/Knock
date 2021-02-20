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
	            'name', 'CurrentColour', 'CoverRectOpacity'

	CardDimensions = None
	DefaultFillColour = None

	def __init__(self, position, SurfaceDimensions=None, RectList=None,
	             Dimensions=None, OpacityRequired=False, FillColour=None,
	             CoverRectOpacity=0):

		self.pos = position

		if SurfaceDimensions:
			self.AddSurf(SurfaceDimensions, position, OpacityRequired)

		self.AddRectList(RectList, CoverRectOpacity)
		self.fill(FillColour if FillColour else self.DefaultFillColour)

		if Dimensions:
			self.midpoint = Dimensions[0] // 2

	def NewSurfaceSize(self, NewSurfaceDimensions, position, OpacityRequired=False, RectList=None):
		if NewSurfaceDimensions != self.Dimensions:
			self.AddSurf(NewSurfaceDimensions, position, OpacityRequired)
			self.AddRectList(RectList, self.CoverRectOpacity)

		self.fill(self.CurrentColour)
		self.midpoint = NewSurfaceDimensions[0] // 2

	def AddSurf(self, SurfaceDimensions, pos=None, OpacityRequired=False):
		self.Dimensions = SurfaceDimensions
		self.surf = Surface(SurfaceDimensions)

		if OpacityRequired:
			self.surf = self.surf.convert_alpha()

		if pos:
			self.pos = pos

		self.surfandpos = (self.surf, self.pos)

	def ShiftPos(self, PosIndex, Shift):
		self.pos[PosIndex] += Shift
		self.surfandpos = (self.surf, self.pos)

	def ResetPos(self):
		self.pos = [0, 0]
		self.surfandpos = (self.surf, self.pos)

	def AddRectList(self, Positions, CoverRectOpacity):
		self.RectList = [Rect(*Position, *self.CardDimensions) for Position in Positions] if Positions else []
		args = (self.CardDimensions, CoverRectOpacity)
		self.CoverRects = CoverRectList([CoverRect(rect, *args) for rect in self.RectList])

	@classmethod
	def AddDefaults(cls, CardDimensions, DefaultFill):
		cls.CardDimensions = CardDimensions
		cls.DefaultFillColour = DefaultFill

	def ClearRectList(self):
		self.RectList.clear()
		self.CoverRects.clear()

	def SetCoverRectOpacity(self, opacity):
		self.CoverRects.SetOpacity(opacity)
		self.CoverRectOpacity = opacity

	def fill(self, colour):
		self.surf.fill(colour)
		self.CoverRects.fill(colour)
		self.CurrentColour = colour

	def blit(self, *args):
		self.surf.blit(*args)

	def blits(self, *args):
		self.surf.blits(*args)


class CoverRect(object):
	__slots__ = 'surf', 'rect', 'surfandrect'

	def __init__(self, rect, CardDimensions, Opacity):
		self.surf = Surface(CardDimensions)
		self.rect = rect
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

	__slots__ = 'font', 'linesize', 'Cursor'

	def __init__(self, font):
		self.font = font
		self.linesize = font.get_linesize()
		self.Cursor = Surface((3, self.linesize))
		self.Cursor.fill((0, 0, 0))

	def render(self, *args):
		return self.font.render(*args)

	def size(self, text):
		return self.font.size(text)
