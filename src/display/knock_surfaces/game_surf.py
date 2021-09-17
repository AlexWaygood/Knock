from __future__ import annotations
from typing import TYPE_CHECKING, Any, Final, TypeVar

from src.display.abstract_surfaces import BaseKnockSurface
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.faders import ColourFader

from src import Dimensions, config, Position, Vector
from src.static_constants import DimensionConstants
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT
from pygame.key import get_pressed as pg_key_get_pressed

if TYPE_CHECKING:
	import src.special_knock_types as skt

# noinspection PyTypeChecker
G = TypeVar('G', bound='GameSurface')


# Controls how much an arrow-key press will move the game surface during gameplay.
ARROW_KEY_NUDGE_AMOUNT: Final = 20

# Controls the start fill colour (used as a key for a ColourFader object)
START_FILL_COLOUR: Final = 'MenuScreen'

# Stops the user resizing the screen into a silly shape
MIN_WIDTH_TO_HEIGHT_RATIO: Final = 1.7

# Stops the user resizing the screen into a silly shape
MAX_WIDTH_TO_HEIGHT_RATIO: Final = 2.2


# noinspection PyAttributeOutsideInit
class GameSurface(BaseKnockSurface):
	__slots__ = (
		'window_dimensions', 'min_rect_width', 'min_rect_height', 'MovementLookup', 'fill_fade', 'scrollwheel',
		'hand', 'surfandpos', 'topleft', 'colour'
	)

	def __init__(self, /, *, start_colour: skt.Colour) -> None:
		super().__init__()
		self.colour = start_colour
		SurfaceCoordinator.game_surf = self
		self.fill_fade = ColourFader(START_FILL_COLOUR)
		self.scrollwheel: skt.OptionalScrollwheel = None

		self.position = Position(x=0, y=0)
		self.dimensions = config.screen_size

		self.window_dimensions = config.screen_size
		self.min_rect_width = DimensionConstants.MIN_GAME_WIDTH
		self.min_rect_height = DimensionConstants.MIN_GAME_HEIGHT

		self.get_surf_and_pos()
		self.hand: skt.OptionalClientHand = None

	def get_surf_and_pos(self, /) -> None:
		super().get_surf_and_pos()
		self.topleft = self.attrs.topleft

	def update(self, /, **kwargs: Any) -> skt.Blittable:
		if self.scrollwheel.is_moving:
			self.mouse_move(self.scrollwheel.get_movement())

		self.fill()
		SurfaceCoordinator.update_all()
		return self.surfandpos

	def fill(self, /) -> None:
		self.colour = self.fill_fade.get_colour()
		self.surf.fill(self.colour)

	def tidy_up(self, /) -> None:
		self.topleft = self.position
		self.attrs.rect.topleft = self.topleft
		self.surfandpos = (self.surf, self.attrs.rect)

	def nudge_up(self, /, *, arrow_shift: bool = True, tidy_up_needed: bool = True) -> None:
		self.y_shift(ARROW_KEY_NUDGE_AMOUNT, arrow_shift=arrow_shift, tidy_up_needed=tidy_up_needed)

	def nudge_down(self, /, *, arrow_shift: bool = True, tidy_up_needed: bool = True) -> None:
		self.y_shift(-ARROW_KEY_NUDGE_AMOUNT, arrow_shift=arrow_shift, tidy_up_needed=tidy_up_needed)

	def nudge_left(self, /, *, arrow_shift: bool = True, tidy_up_needed: bool = True) -> None:
		self.x_shift(-ARROW_KEY_NUDGE_AMOUNT, arrow_shift=arrow_shift, tidy_up_needed=tidy_up_needed)

	def nudge_right(self, /, *, arrow_shift: bool = True, tidy_up_needed: bool = True) -> None:
		self.x_shift(ARROW_KEY_NUDGE_AMOUNT, arrow_shift=arrow_shift, tidy_up_needed=tidy_up_needed)

	def mouse_move(self: G, motion: skt.Position) -> G:
		self.x_shift(motion[0], tidy_up_needed=False).y_shift(motion[1])
		return self

	def x_shift(self: G, amount: float, /, *, arrow_shift: bool = False, tidy_up_needed: bool = True) -> G:
		(x_coord, y_coord), (width, height) = self.position, self.dimensions
		proposed_new_x_coord = x_coord + amount

		new_x_coord = (
			min(config.screen_size.width, proposed_new_x_coord) if amount > 0 else max(-width, proposed_new_x_coord)
		)

		self.hand.move_colliderects(Vector((new_x_coord - x_coord), 0))
		self.position = Position(new_x_coord, y_coord)

		if arrow_shift:
			if (KeysPressed := pg_key_get_pressed())[K_UP]:
				self.nudge_up(arrow_shift=False, tidy_up_needed=False)
			elif KeysPressed[K_DOWN]:
				self.nudge_down(arrow_shift=False, tidy_up_needed=False)

		if tidy_up_needed:
			self.tidy_up()

		return self

	def y_shift(self: G, amount: float, /, *, arrow_shift: bool = False, tidy_up_needed: bool = True) -> G:
		(x_coord, y_coord), (width, height) = self.position, self.dimensions
		proposed_new_y_coord = y_coord + amount

		if amount > 0:
			new_y_coord = min(config.screen_size.height, proposed_new_y_coord)
		else:
			new_y_coord = max(-height, proposed_new_y_coord)

		self.hand.move_colliderects(Vector(0, (new_y_coord - y_coord)))
		self.position = Position(x_coord, new_y_coord)

		if arrow_shift:
			if (KeysPressed := pg_key_get_pressed())[K_LEFT]:
				self.nudge_right(arrow_shift=False, tidy_up_needed=False)
			elif KeysPressed[K_RIGHT]:
				self.nudge_left(arrow_shift=False, tidy_up_needed=False)

		if tidy_up_needed:
			self.tidy_up()

		return self

	def move_to_centre(self, /) -> None:
		(x, y), (width, height), (window_width, window_height) = self.position, self.dimensions, self.window_dimensions
		new_x = (window_width / 2) - (width / 2)
		new_y = (window_height / 2) - (height / 2)
		self.hand.move_colliderects(Vector((new_x - x), (new_y - y)))
		self.position = Position(new_x, new_y)
		self.tidy_up()

	def new_window_size(
			self,
			window_x: int,
			window_y: int,
			reset_pos: bool
	) -> skt.Position:

		new_width, new_height = window_x, window_y
		min_rect_width, min_rect_height = self.min_rect_width, self.min_rect_height

		rect_width = (new_width if new_width >= min_rect_width else min_rect_width)
		rect_height = (new_height if new_height >= min_rect_height else min_rect_height)

		if (rect_width / rect_height) < MIN_WIDTH_TO_HEIGHT_RATIO:
			rect_height = rect_width / MIN_WIDTH_TO_HEIGHT_RATIO
		elif (rect_width / rect_height) > MAX_WIDTH_TO_HEIGHT_RATIO:
			rect_width = rect_height * MAX_WIDTH_TO_HEIGHT_RATIO

		(window_width, window_height), (x, y) = self.window_dimensions, self.position
		x = 0 if reset_pos or rect_width == new_width else (new_width * (x / window_width))
		y = 0 if reset_pos or rect_height == new_height else (new_height * (y / window_height))

		self.position = Position(x, y)
		self.dimensions = Dimensions(new_width, new_height)
		self.get_surf_and_pos()
		self.get_surf()

		return new_width, new_height

	def __repr__(self) -> str:
		return f'''\
GameSurf object, an intermediate surf all things are blitted onto before being blitted onto the screen. Current state:
-x: {self.x}.
-y: {self.y}.
-Width: {self.width}.
-Height: {self.height}.
-window_width: {self.window_width}.
-window_height: {self.window_height}.
-min_rect_width: {self.min_rect_width}.
-min_rect_height: {self.min_rect_height}.
-Attrs: {self.attrs}
-Surf: {self.surf}
-Surfandpos: {self.surfandpos}

'''
