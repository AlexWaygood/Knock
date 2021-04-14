from __future__ import annotations
from typing import TYPE_CHECKING

from src.display.abstract_surfaces.base_knock_surface import BaseKnockSurface
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.faders import ColourFader

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT
from pygame.key import get_pressed as pg_key_get_pressed

if TYPE_CHECKING:
	from src.special_knock_types import OptionalClientHand, OptionalScrollwheel, Position, Colour, Blittable


ARROW_KEY_NUDGE_AMOUNT = 20         # Controls how much an arrow-key press will move the game surface during gameplay.
START_FILL_COLOUR = 'MenuScreen'    # Controls the start fill colour (used as a key for a ColourFader object)
MIN_WIDTH_TO_HEIGHT_RATIO = 1.7     # Stops the user resizing the screen into a silly shape
MAX_WIDTH_TO_HEIGHT_RATIO = 2.2     # Stops the user resizing the screen into a silly shape


# noinspection PyAttributeOutsideInit
class GameSurface(BaseKnockSurface):
	__slots__ = 'WindowWidth', 'WindowHeight', 'MinRectWidth', 'MinRectHeight', 'MovementLookup', 'FillFade', \
	            'scrollwheel', 'Hand', 'surfandpos', 'topleft', 'colour'

	def __init__(
			self,
			StartColour: Colour,
			WindowWidth: int,
			WindowHeight: int,
			MinRectWidth: int,
			MinRectHeight: int
	):

		super().__init__()
		self.colour = StartColour
		SurfaceCoordinator.GameSurf = self
		self.FillFade = ColourFader(START_FILL_COLOUR)
		self.scrollwheel: OptionalScrollwheel = None

		self.x = 0
		self.y = 0
		self.Width = WindowWidth
		self.Height = WindowHeight

		self.WindowWidth = WindowWidth
		self.WindowHeight = WindowHeight
		self.MinRectWidth = MinRectWidth
		self.MinRectHeight = MinRectHeight

		self.SurfAndPos()
		self.Hand: OptionalClientHand = None

	def SurfAndPos(self) -> None:
		super().SurfAndPos()
		self.topleft = self.attrs.topleft

	def Update(self) -> Blittable:
		if self.scrollwheel.IsMoving():
			self.MouseMove(self.scrollwheel.GetMovement())

		self.fill()
		SurfaceCoordinator.UpdateAll()
		return self.surfandpos

	def fill(self) -> None:
		self.colour = self.FillFade.GetColour()
		self.surf.fill(self.colour)

	def TidyUp(self) -> None:
		self.topleft = (self.x, self.y)
		self.attrs.rect.topleft = self.topleft
		self.surfandpos = (self.surf, self.attrs.rect)

	def NudgeUp(self, ArrowShift: bool = True, TidyUpNeeded: bool = True):
		self.YShift(ARROW_KEY_NUDGE_AMOUNT, ArrowShift=ArrowShift,  TidyUpNeeded=TidyUpNeeded)

	def NudgeDown(self, ArrowShift: bool = True, TidyUpNeeded: bool = True):
		self.YShift(-ARROW_KEY_NUDGE_AMOUNT, ArrowShift=ArrowShift,  TidyUpNeeded=TidyUpNeeded)

	def NudgeLeft(self, ArrowShift: bool = True, TidyUpNeeded: bool = True):
		self.XShift(-ARROW_KEY_NUDGE_AMOUNT, ArrowShift=ArrowShift,  TidyUpNeeded=TidyUpNeeded)

	def NudgeRight(self, ArrowShift: bool = True, TidyUpNeeded: bool = True):
		self.XShift(ARROW_KEY_NUDGE_AMOUNT, ArrowShift=ArrowShift, TidyUpNeeded=TidyUpNeeded)

	def MouseMove(self, Motion: Position):
		self.XShift(Motion[0], TidyUpNeeded=False).YShift(Motion[1])
		return self

	def XShift(
			self,
			Amount: float,
			ArrowShift: bool = False,
			TidyUpNeeded: bool = True
	):

		NewCoordinate = self.x + Amount
		NewCoordinate = min(self.WindowWidth, NewCoordinate) if Amount > 0 else max(-self.Width, NewCoordinate)
		self.Hand.MoveColliderects((NewCoordinate - self.x), 0)
		self.x = NewCoordinate

		if ArrowShift:
			if (KeysPressed := pg_key_get_pressed())[K_UP]:
				self.NudgeUp(ArrowShift=False, TidyUpNeeded=False)
			elif KeysPressed[K_DOWN]:
				self.NudgeDown(ArrowShift=False, TidyUpNeeded=False)

		if TidyUpNeeded:
			self.TidyUp()

		return self

	def YShift(
			self,
			Amount: float,
			ArrowShift: bool = False,
			TidyUpNeeded: bool = True
	):

		NewCoordinate = self.y + Amount
		NewCoordinate = min(self.WindowHeight, NewCoordinate) if Amount > 0 else max(-self.Height, NewCoordinate)
		self.Hand.MoveColliderects(0, (NewCoordinate - self.y))
		self.y = NewCoordinate

		if ArrowShift:
			if (KeysPressed := pg_key_get_pressed())[K_LEFT]:
				self.NudgeRight(ArrowShift=False, TidyUpNeeded=False)
			elif KeysPressed[K_RIGHT]:
				self.NudgeLeft(ArrowShift=False, TidyUpNeeded=False)

		if TidyUpNeeded:
			self.TidyUp()

		return self

	def MoveToCentre(self) -> None:
		NewX = (self.WindowWidth / 2) - (self.Width / 2)
		NewY = (self.WindowHeight / 2) - (self.Height / 2)
		self.Hand.MoveColliderects((NewX - self.x), (NewY - self.y))
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

		if (RectWidth / RectHeight) < MIN_WIDTH_TO_HEIGHT_RATIO:
			RectHeight = RectWidth / MIN_WIDTH_TO_HEIGHT_RATIO
		elif (RectWidth / RectHeight) > MAX_WIDTH_TO_HEIGHT_RATIO:
			RectWidth = RectHeight * MAX_WIDTH_TO_HEIGHT_RATIO

		self.Width, self.Height = RectWidth, RectHeight
		self.x = 0 if ResetPos or self.Width == NewWidth else (NewWidth * (self.x / self.WindowWidth))
		self.y = 0 if ResetPos or self.Height == NewHeight else (NewHeight * (self.y / self.WindowHeight))

		self.WindowWidth = NewWidth
		self.WindowHeight = NewHeight

		self.SurfAndPos()
		self.GetSurf()

		return NewWidth, NewHeight

	def __repr__(self) -> str:
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
