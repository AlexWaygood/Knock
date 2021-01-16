from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg


class GameSurface(object):
	"""

	Class for holding data about the game surface,
	an intermediate surface onto which all other surfaces are blitted.

	"""

	__slots__ = 'x', 'y', 'RectWidth', 'RectHeight', 'surf', 'rect', 'surfandpos', 'WindowWidth', 'WindowHeight', \
	            'MovementLookup'

	MinRectWidth = ()
	MinRectHeight = ()
	DefaultFillColour = ()

	def __init__(self, WindowWidth, WindowHeight):

		self.x = 0
		self.y = 0
		self.RectWidth = WindowWidth
		self.RectHeight = WindowHeight
		self.WindowWidth = WindowWidth
		self.WindowHeight = WindowHeight
		self.SurfAndRect(self.DefaultFillColour)

		self.MovementLookup = {
			pg.K_LEFT: lambda foo: foo.XShift(20, ArrowShift=True),
			pg.K_RIGHT: lambda foo: foo.XShift(-20, ArrowShift=True),
			pg.K_UP: lambda foo: foo.YShift(20, ArrowShift=True),
			pg.K_DOWN: lambda foo: foo.YShift(-20, ArrowShift=True)
		}

	def SurfAndRect(self, FillColour):
		self.surf = pg.Surface((self.RectWidth, self.RectHeight))
		self.surf.fill(FillColour)
		self.rect = pg.Rect(self.x, self.y, self.RectWidth, self.RectHeight)
		self.surfandpos = (self.surf, self.rect)

	def ArrowKeyMove(self, EvKey):
		with self:
			self.MovementLookup[EvKey](self)
		return self

	def MouseMove(self, Motion):
		self.XShift(Motion[0]).YShift(Motion[1])
		return self

	def ScrollwheelDownMove(self, ScrollwheelDownPos, MousePos):
		DownX, DownY, MouseX, MouseY = *ScrollwheelDownPos, *MousePos
		self.XShift((DownX - MouseX) / 200)
		self.YShift((DownY - MouseY) / 200)
		return self

	def XShift(self, Amount, ArrowShift=False):
		NewCoordinate = self.x + Amount
		self.x = min(self.WindowWidth, NewCoordinate) if Amount > 0 else max(-self.RectWidth, NewCoordinate)
		self.rect.topleft = (self.x, self.y)
		self.surfandpos = (self.surf, self.rect)

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_UP]:
				self.YShift(20)
			elif pg.key.get_pressed()[pg.K_DOWN]:
				self.YShift(-20)

		return self

	def YShift(self, Amount, ArrowShift=False):
		NewCoordinate = self.y + Amount
		self.y = min(self.WindowHeight, NewCoordinate) if Amount > 0 else max(-self.RectHeight, NewCoordinate)
		self.rect.topleft = (self.x, self.y)
		self.surfandpos = (self.surf, self.rect)

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_LEFT]:
				self.XShift(20)
			elif pg.key.get_pressed()[pg.K_RIGHT]:
				self.XShift(-20)

		return self

	def NewWindowSize(self, NewWindowDimensions, FillColour):
		NewWindowWidth, NewWindowHeight = NewWindowDimensions
		NewRectWidth, NewRectHeight = (NewWindowWidth / 2), (NewWindowHeight / 2)

		self.RectWidth = (NewRectWidth if NewRectWidth >= self.MinRectWidth else self.MinRectWidth)
		self.RectHeight = (NewRectHeight if NewRectHeight >= self.MinRectHeight else self.MinRectHeight)

		self.x = NewWindowWidth * (self.x / self.WindowWidth)
		self.y = NewWindowHeight * (self.y / self.WindowHeight)

		self.WindowWidth = NewWindowWidth
		self.WindowHeight = NewWindowHeight

		self.SurfAndRect(FillColour)
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		return True if not exc_type or exc_type is KeyError else False

	@classmethod
	def AddDefaults(cls, MinRectWidth, MinRectHeight, DefaultFill):
		cls.MinRectWidth = MinRectWidth
		cls.MinRectHeight = MinRectHeight
		cls.DefaultFillColour = DefaultFill

	def fill(self, *args):
		self.surf.fill(*args)

	def blit(self, *args):
		self.surf.blit(*args)

	def blits(self, *args):
		self.surf.blits(*args)
