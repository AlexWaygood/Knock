"""Several classes that are themselves wrappers around pygame classes, to make the client script cleaner"""

from collections import UserList
from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import Surface, Rect


class SurfaceAndPosition(object):
	"""Class for holding data about various surfaces that will be used frequently in the game"""

	__slots__ = 'surf', 'pos', 'surfandpos', 'RectList', 'midpoint', 'CoverRects'

	CardDimensions = None
	DefaultFillColour = None

	def __init__(self, SurfaceDimensions=None, position=None, RectList=None,
	             Dimensions=None, OpacityRequired=False, FillColour=None):

		if position:
			self.pos = position

		if SurfaceDimensions:
			self.AddSurf(SurfaceDimensions, position, OpacityRequired, FillColour)

		if RectList:
			self.AddRectList(RectList)

		if Dimensions:
			self.midpoint = Dimensions[0] // 2

	def AddSurf(self, SurfaceDimensions, pos=None, OpacityRequired=False, FillColour=None):
		self.surf = Surface(SurfaceDimensions)

		if OpacityRequired:
			self.surf = self.surf.convert_alpha()

		self.surf.fill(FillColour if FillColour else self.DefaultFillColour)

		if pos:
			self.pos = pos

		self.surfandpos = (self.surf, self.pos)

	def AddRectList(self, Positions):
		"""Only really used for the Hand surface"""
		self.RectList = [Rect(*Position, *self.CardDimensions) for Position in Positions]
		CoverRects = [CoverRect(self.CardDimensions, self.pos, RectOnSurface) for RectOnSurface in self.RectList]
		self.CoverRects = CoverRectList(CoverRects)

	@classmethod
	def AddCardDimensions(cls, CardDimensions):
		cls.CardDimensions = CardDimensions

	@classmethod
	def AddDefaultFillColour(cls, Colour):
		cls.DefaultFillColour = Colour

	def ClearRectList(self):
		self.RectList.clear()
		self.CoverRects.clear()

	def GetCoverRects(self):
		return self.CoverRects.GetCoverRects()

	def SetCoverRectOpacity(self, *args):
		self.CoverRects.SetOpacity(*args)

	def fill(self, *args):
		self.surf.fill(*args)

	def blit(self, *args):
		self.surf.blit(*args)

	def blits(self, *args):
		self.surf.blits(*args)


class CoverRect(object):
	def __init__(self, CardDimensions, ParentSurfacePos, RectOnSurface, defaultcolour=(128, 0, 0)):
		self.surf = Surface(CardDimensions)
		self.rect = RectOnSurface.move(*ParentSurfacePos)
		self.surf.fill(defaultcolour)
		self.surfandrect = (self.surf, self.rect)

	def set_alpha(self, *args):
		self.surf.set_alpha(*args)


class CoverRectList(UserList):
	def __init__(self, data):
		super().__init__()
		self.data = data
		self.coverrects = self.data

	def SetOpacity(self, *args):
		for cv in self.coverrects:
			cv.set_alpha(*args)

	def GetCoverRects(self):
		return [cv.surfandrect for cv in self.coverrects]


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
