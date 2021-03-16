from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from src.display.abstract_surfaces.base_knock_surface import BaseKnockSurface
from src.display.abstract_surfaces.surface_coordinator import SurfaceCoordinator
from src.display.faders import ColourFader
from src.display.colour_scheme import ColourScheme

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame import locals as pg_locals
from pygame.key import get_pressed as pg_key_get_pressed

if TYPE_CHECKING:
	from src.players.hand import Hand
	from src.special_knock_types import Colour, Position
	from src.display.mouse.mouse import Scrollwheel


# noinspection PyAttributeOutsideInit
class GameSurface(BaseKnockSurface, SurfaceCoordinator):
	__slots__ = 'WindowWidth', 'WindowHeight', 'MinRectWidth', 'MinRectHeight', 'MovementLookup', 'FillFade', \
	            'scrollwheel', 'Hand', 'surfandpos', 'topleft'

	def __init__(self,
	             WindowWidth: int,
	             WindowHeight: int,
	             MinRectWidth: int,
	             MinRectHeight: int):

		self.colour: Colour = ColourScheme.OnlyColourScheme.MenuScreen
		super().__init__()
		SurfaceCoordinator.GameSurf = self
		self.FillFade = ColourFader()
		self.scrollwheel: Optional[Scrollwheel] = None

		self.x = 0
		self.y = 0
		self.Width = WindowWidth
		self.Height = WindowHeight

		self.WindowWidth = WindowWidth
		self.WindowHeight = WindowHeight
		self.MinRectWidth = MinRectWidth
		self.MinRectHeight = MinRectHeight

		self.SurfAndPos()
		self.Hand: Optional[Hand] = None

	def SurfAndPos(self):
		super().SurfAndPos()
		self.topleft = self.attrs.topleft

	def Update(self, ForceUpdate: bool = False):
		if self.scrollwheel.IsMoving():
			XMove, YMove = self.scrollwheel.GetMovement()
			self.XShift(XMove, TidyUpNeeded=False)
			self.YShift(YMove)

		self.fill()
		SurfaceCoordinator.UpdateAll()
		return self.surfandpos

	def fill(self):
		if c := self.FillFade.GetColour():
			self.colour = c
		self.surf.fill(self.colour)

	def TidyUp(self):
		self.topleft = (self.x, self.y)
		self.attrs.rect.topleft = self.topleft
		self.surfandpos = (self.surf, self.attrs.rect)

	def NudgeUp(self):
		self.YShift(20, ArrowShift=True)

	def NudgeDown(self):
		self.YShift(-20, ArrowShift=True)

	def NudgeLeft(self):
		self.XShift(-20, ArrowShift=True)

	def NudgeRight(self):
		self.XShift(20, ArrowShift=True)

	def MouseMove(self, Motion: Position):
		self.XShift(Motion[0], TidyUpNeeded=False).YShift(Motion[1])
		return self

	def XShift(self,
	           Amount: float,
	           ArrowShift: bool = False,
	           TidyUpNeeded: bool = True):

		NewCoordinate = self.x + Amount
		NewCoordinate = min(self.WindowWidth, NewCoordinate) if Amount > 0 else max(-self.Width, NewCoordinate)

		for card in self.Hand:
			card.colliderect.move_ip((NewCoordinate - self.x), 0)

		self.x = NewCoordinate

		if ArrowShift:
			KeysPressed = pg_key_get_pressed()

			if KeysPressed[pg_locals.K_UP]:
				self.YShift(20, TidyUpNeeded=False)
			elif KeysPressed[pg_locals.K_DOWN]:
				self.YShift(-20, TidyUpNeeded=False)

		if TidyUpNeeded:
			self.TidyUp()

		return self

	def YShift(self,
	           Amount: float,
	           ArrowShift: bool = False,
	           TidyUpNeeded: bool = True):

		NewCoordinate = self.y + Amount
		NewCoordinate = min(self.WindowHeight, NewCoordinate) if Amount > 0 else max(-self.Height, NewCoordinate)

		for card in self.Hand:
			card.colliderect.move_ip(0, (NewCoordinate - self.y))

		self.y = NewCoordinate

		if TidyUpNeeded:
			self.TidyUp()

		if ArrowShift:
			KeysPressed = pg_key_get_pressed()

			if KeysPressed[pg_locals.K_LEFT]:
				self.XShift(20, TidyUpNeeded=False)
			elif KeysPressed[pg_locals.K_RIGHT]:
				self.XShift(-20, TidyUpNeeded=False)

		return self

	def MoveToCentre(self):
		NewX = (self.WindowWidth / 2) - (self.Width / 2)
		NewY = (self.WindowHeight / 2) - (self.Height / 2)

		for card in self.Hand:
			card.colliderect.move_ip((NewX - self.x), (NewY - self.y))

		self.x, self.y = NewX, NewY
		self.TidyUp()

	def NewWindowSize(
			self,
			WindowX: int,
			WindowY: int,
			ResetPos: bool
	):

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

	def __repr__(self):
		return f'''\
GameSurf object, an intermediate surf all things are blitted onto before being blitted onto the screen. Current state:
-x: {self.x}.
-y: {self.y}.
-Width: {self.Width}.
-Height: {self.Height}.
-WindowWidth: {self.WindowWidth}.
-WindowHeight: {self.WindowHeight}.
-MinRectWidth: {self.MinRectWidth}.
-MinRectHeight: {self.MinRectHeight}.
-Attrs: {self.attrs}
-Surf: {self.surf}
-Surfandpos: {self.surfandpos}

'''
