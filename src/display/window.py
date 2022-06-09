"""A class representing the window for the game."""

from src import Dimensions, DataclassyReprBase, classmethod_property, cached_classmethod_property
from src.static_constants import DimensionConstants, DIMENSIONS_OF_CARD_IMAGES_ON_HARD_DRIVE
from src.utils.sequence_proxy import SequenceProxy
from functools import lru_cache
from os import path
from logging import getLogger
from fractions import Fraction
from math import ceil
from typing import Callable, TypeVar, NamedTuple, Annotated
import pygame
from enum import Enum, IntEnum


logger = getLogger(__name__)
OnResizeFunc = Callable[[Dimensions], None]
C = TypeVar('C', bound=OnResizeFunc)
# noinspection PyTypeChecker
W = TypeVar('W', bound='Window')


def get_screen_size() -> Dimensions:
	"""Try to calculate the size of the client's screen, fall back to default values if that doesn't work."""

	try:
		from screeninfo import get_monitors
	except ModuleNotFoundError:
		# Default to some dimensions that we know the game works okay with.
		return Dimensions(DimensionConstants.DEFAULT_MAX_WIDTH, DimensionConstants.DEFAULT_MAX_HEIGHT)
	else:
		monitor = get_monitors()[0]
		return Dimensions(monitor.width, monitor.height)


# noinspection PyTypeChecker
G = TypeVar('G', bound='GameDimensions')


class GameDimensions(NamedTuple):
	"""A tuple describing the dimensions of the game."""

	window_margin: Annotated[int, "The space between the left edge of the screen and the left edge of the game surface"]
	card_width: Annotated[int, "The width we want cards to be on the game surface"]
	card_height: Annotated[int, "The height we want cards to be on the game surface"]
	card_image_resize_ratio: Annotated[Fraction, "The ratio by which we need to resize the card images by"]

	@classmethod
	@lru_cache
	def calculate(
			cls: type[G],
			*,
			window_dimensions: Dimensions,
			current_card_dimensions: Dimensions = DIMENSIONS_OF_CARD_IMAGES_ON_HARD_DRIVE
	) -> G:
		"""Calculate the window margin, card height, card width, and ratio by which the card images need to be resized.
		This function is used both at the beginning of the game and midway through the game.
		"""

		# Calculate the required size of the card images,
		# based on various ratios of surfaces that will appear on the screen.

		# Lots of "magic numbers" here,
		# based purely on the principle of "keep the proportions that look good on my laptop".

		(game_width, game_height), (current_card_width, current_card_height) = window_dimensions, current_card_dimensions

		# The window margin is the space between the left edge of the screen and the left edge of the game surface.
		window_margin = int(game_width * Fraction(15, 683))

		# The height we want cards to be on the game surface.
		new_card_height = ceil(min(((game_height // Fraction(768, 150)) - window_margin), (game_height // 5.5)))

		# The width we want cards to be on the game surface.
		new_card_width = ceil(new_card_height * Fraction(current_card_width, current_card_height))

		# The ratio by which we need to resize the card images by.
		card_image_resize_ratio = Fraction(current_card_height, new_card_height)

		# noinspection PyArgumentList
		return cls(
			window_margin=window_margin,
			card_width=new_card_width,
			card_height=new_card_height,
			card_image_resize_ratio=card_image_resize_ratio
		)


class WindowCaptions(str, Enum):
	"""Enumeration of the captions the window might have."""

	ON_STARTUP = 'INITIALISING, PLEASE WAIT...'
	DEFAULT = 'Knock (made by Alex Waygood)'
	CONNECTION_BROKEN = 'LOST CONNECTION WITH THE SERVER'


class WindowModes(IntEnum):
	"""Enumeration of the possible window modes."""

	FULLSCREEN = pygame.FULLSCREEN
	RESIZABLE = pygame.RESIZABLE


# noinspection PyPep8Naming,PyMethodParameters
class Window(DataclassyReprBase):
	"""A class representing the window in which the game is played.

	This class knows NOTHING about coordinating the rest of the display elements.
	"""

	MINIMUM_DIMENSIONS = Dimensions(10, 10)
	MINIMUM_WINDOW_WIDTH, MINIMUM_WINDOW_HEIGHT = MINIMUM_DIMENSIONS
	MAXIMUM_DIMENSIONS = get_screen_size()
	MAXIMUM_WINDOW_WIDTH, MAXIMUM_WINDOW_HEIGHT = MAXIMUM_DIMENSIONS

	# The amount by which the window size is decreased when exiting fullscreen
	EXIT_FULLSCREEN_TOGGLE_AMOUNT = 100

	# The amount by which the window is resized when zooming in and out
	WINDOW_RESIZE_TOGGLE_AMOUNT = 20

	PYGAME_ICON_FILE_PATH = path.join('Images', 'PygameIcon.png')

	@cached_classmethod_property
	def icon(cls, /) -> pygame.Surface:
		"""Get the window icon.

		This is a property as it should only be computed once,
		but cannot be calculated on first import of this module.
		"""
		return pygame.image.load(cls.PYGAME_ICON_FILE_PATH)

	@classmethod
	def set_pygame_icon(cls, /) -> None:
		"""Set the icon for the window."""
		# noinspection PyTypeChecker
		pygame.display.set_icon(cls.icon)

	# At the start of the game, set the caption to ON_STARTUP
	current_caption = WindowCaptions.ON_STARTUP

	_on_window_resize_funcs: list[OnResizeFunc] = []
	_proxy_for_on_window_resize_funcs: SequenceProxy[OnResizeFunc] = SequenceProxy(_on_window_resize_funcs)

	@classmethod_property
	def on_window_resize_funcs(cls, /) -> SequenceProxy[OnResizeFunc]:
		"""Get a proxy for the functions that are registered as being on_redraw functions."""
		return cls._proxy_for_on_window_resize_funcs

	@classmethod
	def on_window_resize(cls, func: C) -> C:
		"""Decorator to be used on external functions outside this class.
		Using this decorator will register the function to be called every time there is a new window size.

		Parameters
		----------
		func: Callable[[GameDimensions], None]
			An in-place function that accepts a `GameDimensions` tuple.

		Returns
		-------
		The same function, unchanged

		Modifies
		--------
		This class's `_on_window_resize_funcs` list: a list of functions called every time the window size is changed.
		"""

		cls._on_window_resize_funcs.append(func)
		return func

	__slots__ = '_dimensions', 'deactivate_video_resize', 'mode', 'window', 'fill_colour'

	NON_REPR_SLOTS = '_dimensions',

	EXTRA_REPR_ATTRS = (
		'dimensions', 'is_fullscreen', 'is_at_max_size', 'is_at_min_size', 'MINIMUM_DIMENSIONS', 'MAXIMUM_DIMENSIONS'
	)

	def __init__(
			self,
			/,
			*,
			fill_colour,
			window_resizing: bool = True,
			mode: WindowModes = WindowModes.FULLSCREEN,
			deactivate_video_resize: bool = False,
			dimensions: Dimensions = Dimensions(MAXIMUM_WINDOW_WIDTH, MAXIMUM_WINDOW_HEIGHT)
	) -> None:
		"""Create a new window at a certain size."""

		self._dimensions = dimensions
		self.deactivate_video_resize = deactivate_video_resize

		if window_resizing:
			for func in self.on_window_resize_funcs:
				func(dimensions)

		self.mode = mode
		self.window = pygame.display.set_mode(dimensions, flags=mode)
		self.fill(fill_colour)
		pygame.display.update()

	@property
	def dimensions(self, /) -> Dimensions:
		"""Get the dimensions of the window.
		This is a read-only attribute that is set once in the __init__ method of an instance.
		"""

		return self._dimensions

	@property
	def is_fullscreen(self, /) -> bool:
		"""Return `True` if we are in fullscreen mode, else `False`."""
		return self.mode is WindowModes.FULLSCREEN

	@property
	def is_at_max_size(self, /) -> bool:
		"""Return `True` if the window fills the whole screen (NOT the same as being in fullscreen mode)."""
		return self.dimensions == self.MAXIMUM_DIMENSIONS

	@property
	def is_at_min_size(self, /) -> bool:
		"""Return `True` if the window is already at the minimum permitted size, else `False`."""
		return self.dimensions == self.MINIMUM_DIMENSIONS

	def fill(self, colour) -> None:
		"""Fill the window a certain colour."""
		self.window.fill(colour)
		self.fill_colour = colour

	@classmethod
	def on_startup(cls: type[W], /) -> W:
		"""Create a new window on startup of the programme."""
		logger.debug('Launching pygame window.')
		cls.set_pygame_icon()
		COLOUR = ...
		modes = WindowModes
		cls(mode=modes.RESIZABLE, fill_colour=COLOUR)
		cls.restart_display()
		return cls(mode=modes.RESIZABLE, fill_colour=COLOUR, window_resizing=False)

	@classmethod
	def restart_display(cls, /) -> None:
		"""Restart the pygame display module and set the pygame caption/icon to the current caption/icon.
		There is no need to create a new `window` instance.
		"""

		pygame.display.quit()
		pygame.display.init()
		pygame.display.set_caption(cls.current_caption)
		cls.set_pygame_icon()

	@classmethod
	def change_caption(cls, caption: WindowCaptions) -> None:
		"""Change the window caption."""
		cls.current_caption = caption
		pygame.display.set_caption(caption)

	def fullscreen_toggled(self: W, /) -> W:
		"""Toggle in or out of fullscreen.
		This method returns a new window instance; it DOES NOT operate in-place.
		"""

		if self.is_fullscreen:
			return self.zoomed_out_one_notch()

		return self.__class__(
			mode=WindowModes.FULLSCREEN,
			dimensions=self.MAXIMUM_DIMENSIONS,
			deactivate_video_resize=True,
			fill_colour=self.fill_colour
		)

	def zoomed_out_one_notch(self: W, /) -> W:
		"""Create a new window instance that is one notch zoomed out from this one.
		This method returns a new instance. It DOES NOT operate in-place.
		"""

		if self.is_at_min_size:
			# We're already at the minimum permitted size; no need to change anything.
			return self

		current_width, current_height = self.dimensions
		window_toggle_amount = self.WINDOW_RESIZE_TOGGLE_AMOUNT

		proposed_width = current_width - window_toggle_amount
		proposed_height = current_height - window_toggle_amount

		cls = type(self)
		window_modes = WindowModes
		min_width, min_height = min_dimensions = self.MINIMUM_DIMENSIONS
		deactivate_video_resize = False

		# Five possibilities which require different courses of action.

		if self.is_fullscreen:
			# We're exiting fullscreen, so we need to restart the display.
			cls.restart_display()
			new_width, new_height, deactivate_video_resize = proposed_width, proposed_height, True

		elif proposed_width <= min_width and proposed_height <= min_height:
			# We're shrinking to the minimum possible size.
			new_width, new_height = min_dimensions

		elif proposed_width < min_width:
			# 1). Current width is close to minimum width:
			# New width snaps to minimum width, height decreases by toggle amount.
			new_width, new_height = min_width, proposed_height

		elif proposed_height < min_height:
			# 2). Current height is close to minimum height:
			# Width decreases by toggle amount, new height snaps to minimum height.
			new_width, new_height = proposed_width, min_height

		else:
			# 3). Neither is close to their minimum:
			# Both width and height decrease by toggle amount.
			new_width, new_height = proposed_width, proposed_height

		return cls(
			dimensions=Dimensions(new_width, new_height),
			mode=window_modes.RESIZABLE,
			deactivate_video_resize=deactivate_video_resize,
			fill_colour=self.fill_colour
		)

	def zoomed_in_one_notch(self: W, /) -> W:
		"""Create a new window instance that is one notch zoomed in from this one.
		This method returns a new instance. It DOES NOT operate in-place.
		"""

		if self.is_at_max_size:
			# We're already at maximum size; no need to change anything.
			return self

		current_width, current_height = self.dimensions
		window_toggle_amount = self.WINDOW_RESIZE_TOGGLE_AMOUNT

		proposed_width = current_width + window_toggle_amount
		proposed_height = current_height + window_toggle_amount

		max_width, max_height = max_dimensions = self.MAXIMUM_DIMENSIONS

		cls = type(self)
		window_modes = WindowModes

		# These two are only different if we are entering fullscreen,
		# in which case they are set to `True` and window_modes.FULLSCREEN
		deactivate_video_resize, mode = False, window_modes.RESIZABLE

		# Four separate possibilities which require 4 separate courses of action.

		if proposed_width >= max_width and proposed_height >= max_height:
			# 1). We're entering fullscreen after having not been in fullscreen
			# We do NOT need to restart the display -- we only need to do that when EXITING fullscreen.
			new_width, new_height = max_dimensions
			deactivate_video_resize, mode = True, window_modes.FULLSCREEN

		elif proposed_width > max_width:
			# 2). Current width is close to maximum width:
			# New width snaps to maximum width, height increases by toggle amount.
			new_width, new_height = max_width, proposed_height

		elif proposed_height > max_height:
			# 3). Current height is close to maximum height:
			# Width increases by toggle amount, new height snaps to maximum height.
			new_width, new_height = proposed_width, max_height

		else:
			# 4). Neither is close to their maximum:
			# Both width and height increase by toggle amount.
			new_width, new_height = proposed_width, proposed_height

		return cls(
			dimensions=Dimensions(new_width, new_height),
			deactivate_video_resize=deactivate_video_resize,
			mode=mode,
			fill_colour=self.fill_colour
		)

	def after_video_resize_event(self: W, /, *, new_size: Dimensions) -> W:
		"""Respond to a pygame "video resize" event.

		"Video resize" events are triggered on exiting/entering fullscreen as well as manual resizing;
		we only want to create a new window instance after a manual resize.
		"""

		if self.deactivate_video_resize:
			self.deactivate_video_resize = False
			return self

		return self.__class__(
			mode=WindowModes.RESIZABLE,
			dimensions=new_size,
			fill_colour=self.fill_colour
		)
