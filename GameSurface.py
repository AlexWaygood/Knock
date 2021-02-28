from os import environ

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg

from SurfaceBaseClasses import BaseKnockSurface


# noinspection PyAttributeOutsideInit
class GameSurface(BaseKnockSurface):
	__slots__ = 'WindowWidth', 'WindowHeight', 'MinRectWidth', 'MinRectHeight', 'MovementLookup'

	def __init__(self, FillColour, WindowWidth, WindowHeight, MinRectWidth, MinRectHeight):
		super().__init__(FillColour)
		self.x = 0
		self.y = 0
		self.SurfWidth = WindowWidth
		self.SurfHeight = WindowHeight

		self.WindowWidth = WindowWidth
		self.WindowHeight = WindowHeight
		self.MinRectWidth = MinRectWidth
		self.MinRectHeight = MinRectHeight

		self.SurfAndPos()

		self.MovementLookup = {
			pg.K_LEFT: lambda: self.XShift(20, ArrowShift=True),
			pg.K_RIGHT: lambda: self.XShift(-20, ArrowShift=True),
			pg.K_UP: lambda: self.YShift(20, ArrowShift=True),
			pg.K_DOWN: lambda: self.YShift(-20, ArrowShift=True)
		}

	def TidyUp(self):
		self.topleft = (self.x, self.y)
		self.rect.topleft = self.topleft
		self.surfandpos = (self.surf, self.rect)

	def ArrowKeyMove(self, EvKey):
		try:
			self.MovementLookup[EvKey]()
		except KeyError:
			pass

		return self

	def MouseMove(self, Motion):
		self.XShift(Motion[0], TidyUpNeeded=False).YShift(Motion[1])
		return self

	def ScrollwheelDownMove(self, ScrollwheelDownPos):
		# noinspection PyTupleAssignmentBalance
		DownX, DownY, MouseX, MouseY = *ScrollwheelDownPos, *pg.mouse.get_pos()
		self.XShift(((DownX - MouseX) / 200), TidyUpNeeded=False)
		self.YShift((DownY - MouseY) / 200)
		return self

	def XShift(self, Amount, ArrowShift=False, TidyUpNeeded=True):
		NewCoordinate = self.x + Amount
		self.x = min(self.WindowWidth, NewCoordinate) if Amount > 0 else max(-self.SurfWidth, NewCoordinate)

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_UP]:
				self.YShift(20, TidyUpNeeded=False)
			elif pg.key.get_pressed()[pg.K_DOWN]:
				self.YShift(-20, TidyUpNeeded=False)

		if TidyUpNeeded:
			self.TidyUp()

		return self

	def YShift(self, Amount, ArrowShift=False, TidyUpNeeded=True):
		NewCoordinate = self.y + Amount
		self.y = min(self.WindowHeight, NewCoordinate) if Amount > 0 else max(-self.SurfHeight, NewCoordinate)

		if TidyUpNeeded:
			self.TidyUp()

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_LEFT]:
				self.XShift(20, TidyUpNeeded=False)
			elif pg.key.get_pressed()[pg.K_RIGHT]:
				self.XShift(-20, TidyUpNeeded=False)

		return self

	def MoveToCentre(self):
		self.x = (self.WindowWidth / 2) - (self.SurfWidth / 2)
		self.y = (self.WindowHeight / 2) - (self.SurfHeight / 2)
		self.TidyUp()

	def NewWindowSize(self, WindowX, WindowY, ResetPos: int):
		NewWidth, NewHeight = WindowX, WindowY

		RectWidth = (NewWidth if NewWidth >= self.MinRectWidth else self.MinRectWidth)
		RectHeight = (NewHeight if NewHeight >= self.MinRectHeight else self.MinRectHeight)

		if 1.7 > (RectWidth / RectHeight):
			RectHeight = RectWidth / 1.7
		elif 2.2 < (RectWidth / RectHeight):
			RectWidth = RectHeight * 2.2

		self.SurfWidth, self.SurfHeight = RectWidth, RectHeight

		self.x = 0 if ResetPos or self.SurfWidth == NewWidth else (NewWidth * (self.x / self.WindowWidth))
		self.y = 0 if ResetPos or self.SurfHeight == NewHeight else (NewHeight * (self.y / self.WindowHeight))

		self.WindowWidth = NewWidth
		self.WindowHeight = NewHeight

		self.SurfAndPos()
		return self
