from src.Display.AbstractSurfaces.BaseKnockSurface import BaseKnockSurface
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator
from src.Display.Faders import ColourFader
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg


# noinspection PyAttributeOutsideInit
class GameSurface(BaseKnockSurface, SurfaceCoordinator):
	__slots__ = 'WindowWidth', 'WindowHeight', 'MinRectWidth', 'MinRectHeight', 'MovementLookup', 'FillFade', \
	            'scrollwheel', 'Hand', 'surfandpos', 'topleft'

	def __init__(self, FillColour, WindowWidth, WindowHeight, MinRectWidth, MinRectHeight):
		"""
		@type FillColour: tuple
		@type WindowWidth: int
		@type WindowHeight: int
		@type MinRectWidth: int
		@type MinRectHeight: int
		"""

		self.colour = FillColour
		super().__init__()
		self.FillFade = ColourFader()
		self.scrollwheel = None

		self.x = 0
		self.y = 0
		self.Width = WindowWidth
		self.Height = WindowHeight

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

		self.Hand = self.player.Hand

	def SurfAndPos(self):
		super().SurfAndPos()
		self.surfandpos = self.attrs.surfandpos
		self.topleft = self.attrs.topleft

	def Update(self, ForceUpdate=False):
		if self.scrollwheel.IsDown and pg.time.get_ticks() < self.scrollwheel.DownTime + 20:
			# noinspection PyTupleAssignmentBalance
			DownX, DownY, MouseX, MouseY = *self.scrollwheel.DownPos, *pg.mouse.get_pos()
			self.XShift(((DownX - MouseX) / 200), TidyUpNeeded=False)
			self.YShift((DownY - MouseY) / 200)

		self.fill()
		SurfaceCoordinator.UpdateAll()
		return self.surfandpos

	def fill(self):
		if c := self.FillFade.GetColour():
			self.colour = c
		self.attrs.surf.fill(self.colour)

	def TidyUp(self):
		self.topleft = (self.x, self.y)
		self.attrs.rect.topleft = self.topleft
		self.surfandpos = (self.attrs.surf, self.attrs.rect)

	def ArrowKeyMove(self, EvKey: int):
		try:
			self.MovementLookup[EvKey]()
		except KeyError:
			pass

		return self

	def MouseMove(self, Motion):
		self.XShift(Motion[0], TidyUpNeeded=False).YShift(Motion[1])
		return self

	def XShift(self, Amount: int, ArrowShift=False, TidyUpNeeded=True):
		NewCoordinate = self.x + Amount
		NewCoordinate = min(self.WindowWidth, NewCoordinate) if Amount > 0 else max(-self.Width, NewCoordinate)

		for card in self.Hand:
			card.colliderect.move_ip((NewCoordinate - self.x), 0)

		self.x = NewCoordinate

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_UP]:
				self.YShift(20, TidyUpNeeded=False)
			elif pg.key.get_pressed()[pg.K_DOWN]:
				self.YShift(-20, TidyUpNeeded=False)

		if TidyUpNeeded:
			self.TidyUp()

		return self

	def YShift(self, Amount: int, ArrowShift=False, TidyUpNeeded=True):
		NewCoordinate = self.y + Amount
		NewCoordinate = min(self.WindowHeight, NewCoordinate) if Amount > 0 else max(-self.Height, NewCoordinate)

		for card in self.Hand:
			card.colliderect.move_ip(0, (NewCoordinate - self.y))

		self.y = NewCoordinate

		if TidyUpNeeded:
			self.TidyUp()

		if ArrowShift:
			if pg.key.get_pressed()[pg.K_LEFT]:
				self.XShift(20, TidyUpNeeded=False)
			elif pg.key.get_pressed()[pg.K_RIGHT]:
				self.XShift(-20, TidyUpNeeded=False)

		return self

	def MoveToCentre(self):
		NewX = (self.WindowWidth / 2) - (self.Width / 2)
		NewY = (self.WindowHeight / 2) - (self.Height / 2)

		for card in self.Hand:
			card.colliderect.move_ip((NewX - self.x), (NewY - self.y))

		self.x, self.y = NewX, NewY
		self.TidyUp()

	def NewWindowSize(self, WindowX, WindowY, ResetPos):
		"""
		@type WindowX: int
		@type WindowY: int
		@type ResetPos: int
		"""

		NewWidth, NewHeight = WindowX, WindowY

		RectWidth = (NewWidth if NewWidth >= self.MinRectWidth else self.MinRectWidth)
		RectHeight = (NewHeight if NewHeight >= self.MinRectHeight else self.MinRectHeight)

		if 1.7 > (RectWidth / RectHeight):
			RectHeight = RectWidth / 1.7
		elif 2.2 < (RectWidth / RectHeight):
			RectWidth = RectHeight * 2.2

		self.Width, self.Height = RectWidth, RectHeight

		self.x = 0 if ResetPos or self.Width == NewWidth else (NewWidth * (self.x / self.WindowWidth))
		self.y = 0 if ResetPos or self.Height == NewHeight else (NewHeight * (self.y / self.WindowHeight))

		self.WindowWidth = NewWidth
		self.WindowHeight = NewHeight

		self.SurfAndPos()
		return NewWidth, NewHeight
