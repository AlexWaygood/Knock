from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg


class GameSurface(object):
	"""

	Class for holding data about the game surface,
	an intermediate surface onto which all other surfaces are blitted.

	"""

	__slots__ = 'x', 'y', 'RectWidth', 'RectHeight', 'surf', 'rect', 'surfandpos', 'WindowWidth', 'WindowHeight', \
	            'MovementLookup', 'centre', 'Dimensions', 'topleft'

	MinRectWidth = 0
	MinRectHeight = 0

	def __init__(self, WindowWidth, WindowHeight, FillColour):

		self.x = 0
		self.y = 0
		self.RectWidth = WindowWidth
		self.RectHeight = WindowHeight
		self.WindowWidth = WindowWidth
		self.WindowHeight = WindowHeight
		self.SurfAndRect(FillColour)

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
		self.topleft = (self.x, self.y)
		self.Dimensions = (self.RectWidth, self.RectHeight)
		self.surfandpos = (self.surf, self.rect)
		self.centre = ((self.RectWidth / 2), (self.RectHeight / 2))

	def ArrowKeyMove(self, EvKey):
		with self:
			self.MovementLookup[EvKey](self)
		return self

	def MouseMove(self, Motion):
		self.XShift(Motion[0]).YShift(Motion[1])
		return self

	def ScrollwheelDownMove(self, ScrollwheelDownPos):
		DownX, DownY, MouseX, MouseY = *ScrollwheelDownPos, *pg.mouse.get_pos()
		self.XShift((DownX - MouseX) / 200)
		self.YShift((DownY - MouseY) / 200)
		return self

	def XShift(self, Amount, ArrowShift=False):
		NewCoordinate = self.x + Amount
		self.x = min(self.WindowWidth, NewCoordinate) if Amount > 0 else max(-self.RectWidth, NewCoordinate)
		self.TidyUp()

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_UP]:
				self.YShift(20)
			elif pg.key.get_pressed()[pg.K_DOWN]:
				self.YShift(-20)

		return self

	def YShift(self, Amount, ArrowShift=False):
		NewCoordinate = self.y + Amount
		self.y = min(self.WindowHeight, NewCoordinate) if Amount > 0 else max(-self.RectHeight, NewCoordinate)
		self.TidyUp()

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_LEFT]:
				self.XShift(20)
			elif pg.key.get_pressed()[pg.K_RIGHT]:
				self.XShift(-20)

		return self

	def MoveToCentre(self):
		self.x = (self.WindowWidth / 2) - (self.RectWidth / 2)
		self.y = (self.WindowHeight / 2) - (self.RectHeight / 2)
		self.TidyUp()

	def TidyUp(self):
		self.topleft = (self.x, self.y)
		self.rect.topleft = self.topleft
		self.surfandpos = (self.surf, self.rect)

	def NewWindowSize(self, NewWindowDimensions, FillColour, ResetPos=False):
		NewWidth, NewHeight = NewWindowDimensions

		RectWidth = (NewWidth if NewWidth >= self.MinRectWidth else self.MinRectWidth)
		RectHeight = (NewHeight if NewHeight >= self.MinRectHeight else self.MinRectHeight)

		if 1.7 > (RectWidth / RectHeight):
			RectHeight = RectWidth / 1.7
		elif 2.2 < (RectWidth / RectHeight):
			RectWidth = RectHeight * 2.2

		self.RectWidth, self.RectHeight = RectWidth, RectHeight

		self.x = 0 if ResetPos or self.RectWidth == NewWidth else (NewWidth * (self.x / self.WindowWidth))
		self.y = 0 if ResetPos or self.RectHeight == NewHeight else (NewHeight * (self.y / self.WindowHeight))

		self.WindowWidth = NewWidth
		self.WindowHeight = NewHeight

		self.SurfAndRect(FillColour)
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		return bool(not exc_type or exc_type is KeyError)

	@classmethod
	def AddDefaults(cls, MinRectWidth, MinRectHeight):
		cls.MinRectWidth = MinRectWidth
		cls.MinRectHeight = MinRectHeight

	def fill(self, *args):
		self.surf.fill(*args)

	def blit(self, *args):
		self.surf.blit(*args)

	def blits(self, *args):
		self.surf.blits(*args)
