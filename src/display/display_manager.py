from __future__ import annotations

from os import path
from random import randint
from functools import lru_cache
from typing import TYPE_CHECKING, NoReturn, Optional, NamedTuple
from queue import Queue
from collections import deque
from immutables import Map
from aenum import NamedConstant
from logging import getLogger

from src.static_constants import FillColours, CardFaderNames, DimensionConstants

from src import display, DocumentedIntConstants, DocumentedSetConstants
from src.players.players_client import ClientPlayer as Players

from src import Dimensions, config

from pygame import (
	quit as pg_quit,
	locals as pgl,
	display as pgd
)

from pygame.image import load as pg_image_load
from pygame.time import Clock, delay, get_ticks
from pygame.mouse import set_cursor, get_pressed as pg_mouse_get_pressed
from pygame.event import get as pg_event_get
from pygame.key import get_mods as pg_key_get_mods

if TYPE_CHECKING:
	from pygame.event import Event
	from src.special_knock_types import Colour, BlitsList


class WindowConstants(NamedConstant):
	"""String Constants relating to the window caption & icon"""

	PYGAME_ICON_FILE_PATH = path.join('Images', 'PygameIcon.png')
	DEFAULT_WINDOW_CAPTION = 'Knock (made by Alex Waygood)'
	CONNECTION_BROKEN_CAPTION = 'LOST CONNECTION WITH THE SERVER'


class DisplayConstants(DocumentedIntConstants):
	"""Int constants relating to various display settings"""

	SCROLLWHEEL_EVENT_FREQUENCY = 1000, "The milliseconds between each new pygame 'scrollwheel event'"
	FRAME_RATE = 100, "The number of frames per second"
	EXIT_FULLSCREEN_TOGGLE_AMOUNT = 100, "The amount by which the window size is decreased when exiting fullscreen"
	WINDOW_RESIZE_TOGGLE_AMOUNT = 20, "The amount by which the window is resized when zooming in and out"


class KeyConstants(DocumentedSetConstants):
	"""An enumeration of keyboard keys that have special effects in this game."""

	WINDOW_RESIZE_KEYS = frozenset({pgl.K_ESCAPE, pgl.K_TAB}), "Keys used to trigger a 'window resize' event"
	GAME_REMATCH_KEYS = frozenset({pgl.K_SPACE, pgl.K_RETURN}), "Keys used at game-end to trigger a rematch",
	ARROW_KEYS = frozenset({pgl.K_UP, pgl.K_DOWN, pgl.K_LEFT, pgl.K_RIGHT}), "The arrow keys, used for moving around."


LOGGING_FREQUENCY = 1000
CONNECTION_BROKEN_DELAY = 500
DEFAULT_NETWORK_MESSAGE = 'pong'
logger = getLogger(__name__)


class ResizeInfoTuple(NamedTuple):
	"""Return type for `zoom_in_helper` and `zoom_out_helper`"""
	new_dimension: int
	resize_occurred: bool


@lru_cache
def zoom_in_helper(*, new_var: int, old_var: int, screen_size: Dimensions, index: int) -> ResizeInfoTuple:
	if new_var > (s := screen_size[index]):
		new_var = s
	return ResizeInfoTuple(new_dimension=new_var, resize_occurred=(new_var != old_var))


@lru_cache
def zoom_out_helper(*, new_var: int, old_var: int, minimum_dimension: int = 10) -> ResizeInfoTuple:
	if new_var < minimum_dimension:
		new_var = minimum_dimension
	return ResizeInfoTuple(new_dimension=new_var, resize_occurred=(new_var != old_var))


def control_key_down() -> int:
	"""Return `True` if the control key is being held down, else `False`"""
	return pg_key_get_mods() & pgl.KMOD_CTRL


# Subclasses DictLike for easy attribute access in the main client script

class DisplayManager:
	__slots__ = (
		'board_surf', 'scoreboard_surf', 'window_dimensions', 'window',
		'window_icon', 'fullscreen', 'deactivate_video_resize', 'firework_vars', 'display_updates_completed',
		'last_display_log', 'window_caption', 'interactive_scoreboard', 'clock', 'player', 'control_key_functions',
		'arrow_key_functions'
	)

	def __init__(self, /, *, start_colour: Colour) -> None:
		self.window_dimensions = config.screen_size
		self.player = Players.me()
		self.clock = Clock()
		self.last_display_log = 0
		self.display_updates_completed = 0
		self.fullscreen = True  # Technically incorrect, but it fills up the whole screen.
		self.deactivate_video_resize = False
		self.window_caption = 'INITIALISING, PLEASE WAIT...'

		display.Fader.add_colour_scheme()  # Must be done before initialising any Knock surfaces

		# The game_surf Adds itself as a class variable to the SurfaceCoordinator in __init__
		# noinspection PyTypeChecker
		config.GameSurf = display.GameSurface(start_colour=start_colour)
		display.SurfaceCoordinator.add_class_vars(player=self.player)
		display.TextBlitsMixin.add_text_fader()

		self.board_surf = display.BoardSurface()  # Adds itself as a class variable to the SurfaceCoordinator in __init__
		self.scoreboard_surf = display.ScoreboardSurface()
		config.HandSurf = display.HandSurface()
		config.TrumpCardSurf = display.TrumpCardSurface()
		display.SurfaceCoordinator.new_window_size_2()

		config.input_context = display.GameInputContextManager()
		config.typewriter = display.Typewriter([], -1, Queue(), None, None)
		config.Errors = display.Errors(deque(), [], get_ticks(), None)
		config.UserInput = display.TextInput('', None, config.input_context, config.Errors)
		config.Mouse = display.Mouse(scoreboard_button=None, context=config.input_context)
		config.Scrollwheel = config.Mouse.scrollwheel
		config.GameSurf.scrollwheel = config.Mouse.scrollwheel
		self.firework_vars = display.FireworkVars()
		self.interactive_scoreboard = display.InteractiveScoreboard(context=config.input_context)
		self.window_icon = pg_image_load(WindowConstants.PYGAME_ICON_FILE_PATH)

		# A mapping giving the special meaning of keys during gameplay,
		# when the control key is being held down.

		self.control_key_functions = Map({
			# CTRL C -> Move the field of view to the centre of the game.
			pgl.K_c: config.GameSurf.move_to_centre,

			# CTRL Q -> Quit the game.
			pgl.K_q: self.quit_game,

			# CTRL S -> Save the scoreboard as a .csv file.
			pgl.K_s: self.interactive_scoreboard.save,

			# CTRL T -> Take a look at the full scoreboard in a separate window
			# ("T" stands for "table")
			pgl.K_t: self.interactive_scoreboard.show,

			# CTRL V -> paste something into a text-entry field.
			pgl.K_v: config.UserInput.paste_event,

			# CTRL BACKSPACE -> delete a whole word in a text-entry field
			pgl.K_BACKSPACE: config.UserInput.control_backspace_event,

			# CTRL PLUS -> Zoom in
			pgl.K_PLUS: self.zoom_in,

			# CTRL EQUALS -> Zoom in (same button as PLUS)
			pgl.K_EQUALS: self.zoom_in,

			# CTRL MINUS -> Zoom out
			pgl.K_MINUS: self.zoom_out,

			# CTRL UNDERSCORE -> Zoom out (same button as MINUS)
			pgl.K_UNDERSCORE: self.zoom_out
		})

		# Keys relating to moving around the game during gameplay.

		self.arrow_key_functions = Map({
			pgl.K_UP: config.GameSurf.nudge_up,
			pgl.K_DOWN: config.GameSurf.nudge_down,
			pgl.K_LEFT: config.GameSurf.nudge_left,
			pgl.K_RIGHT: config.GameSurf.nudge_right
		})

	def run(self, /) -> NoReturn:
		"""Run the event loop until the end of the game."""

		logger.debug('Launching pygame window.')
		pgd.set_icon(self.window_icon)
		self.initialise_window(pgl.RESIZABLE)
		self.restart_display()
		self.initialise_window(pgl.RESIZABLE)
		set_cursor(pgl.SYSTEM_CURSOR_WAIT)
		display.SurfaceCoordinator.add_surfs()
		config.GameSurf.get_surf()
		self.window_caption = WindowConstants.DEFAULT_WINDOW_CAPTION
		pgd.set_caption(self.window_caption)

		logger.debug('Starting main pygame loop.')
		while True:
			self.update()

	@staticmethod
	def get_hand_rects() -> None:
		config.HandSurf.get_hand_rects()

	@staticmethod
	def clear_hand_rects() -> None:
		config.HandSurf.clear_rect_list()

	@staticmethod
	def activate_hand() -> None:
		"""'Activate' the HandSurf such that it will be blitted to the GameSurf in future frames."""
		config.HandSurf.activate()

	@staticmethod
	def deactivate_hand() -> None:
		"""'Deactivate' the HandSurf such that it will no longer be blitted to the GameSurf."""
		config.HandSurf.deactivate()

	@staticmethod
	def blits(blits_list: BlitsList) -> None:
		config.GameSurf.surf.blits(blits_list)

	def game_initialisation_fade(self, /) -> None:
		"""Fade the window from the menu-screen fill colour to the gameplay fill-colour; fade the scoreboard in."""

		if not config.game.games_played:
			config.GameSurf.fill_fade(FillColours.MENU_SCREEN_FILL_COLOUR, FillColours.GAMEPLAY_FILL_COLOUR, 1000)

		self.scoreboard_surf.real_init()
		self.scoreboard_surf.fill_fade(FillColours.GAMEPLAY_FILL_COLOUR, FillColours.SCOREBOARD_FILL_COLOUR, 1000)

	def round_start_fade(self, /) -> None:
		self.board_surf.activate()
		config.TrumpCardSurf.activate()

		display.TextBlitsMixin.TextFade(
			colour1=FillColours.GAMEPLAY_FILL_COLOUR,
			colour2=FillColours.TEXT_DEFAULT_FILL_COLOUR,
			time_to_take=1000
		)

		config.HandSurf.activate()
		display.OpacityFader.card_fade(
			(CardFaderNames.HAND_CARD_FADE_KEY, CardFaderNames.TRUMP_CARD_FADE_KEY),
			time_to_take=1000,
			fade_in=True
		)

	@staticmethod
	def trick_end_fade() -> None:
		"""Fade the board cards out at the end of the trick."""
		display.OpacityFader.card_fade((CardFaderNames.BOARD_CARD_FADE_KEY,), time_to_take=300, fade_in=False)

	def round_end_fade(self, /) -> None:
		"""Fade the trumpcard and board text out at the end of the round."""

		config.HandSurf.deactivate()

		display.OpacityFader.card_fade((CardFaderNames.TRUMP_CARD_FADE_KEY,), time_to_take=1000, fade_in=False)

		display.TextBlitsMixin.TextFade(
			colour1=FillColours.TEXT_DEFAULT_FILL_COLOUR,
			colour2=FillColours.GAMEPLAY_FILL_COLOUR,
			time_to_take=1000
		)

		config.TrumpCardSurf.deactivate()
		self.board_surf.deactivate()

	def fireworks_sequence(self, /) -> None:
		"""Treat the players to a fireworks display at the end of the game."""

		# fade the screen out incrementally to prepare for the fireworks display
		self.scoreboard_surf.fill_fade(FillColours.SCOREBOARD_FILL_COLOUR, FillColours.GAMEPLAY_FILL_COLOUR, 1000)
		config.GameSurf.fill_fade(FillColours.GAMEPLAY_FILL_COLOUR, FillColours.FIREWORKS_FILL_COLOUR, 1000)

		self.scoreboard_surf.deactivate()

		# This part of the code adapted from code by Adam Binks
		display.FireworkVars.LastFirework = get_ticks()
		duration = self.firework_vars.SecondsDuration * 1000
		display.FireworkVars.EndTime = self.firework_vars.LastFirework + duration
		display.FireworkVars.RandomAmount = randint(*self.firework_vars.Bounds)

		with config.input_context(FireworksInProgress=True):
			delay(duration)
			while get_ticks() < display.FireworkVars.EndTime or display.FireworkParticle.allParticles:
				delay(100)

		# fade the screen back to maroon after the fireworks display.
		config.GameSurf.fill_fade(FillColours.FIREWORKS_FILL_COLOUR, FillColours.GAMEPLAY_FILL_COLOUR, 1000)
		delay(1000)

	def quit_game(self, /) -> NoReturn:
		"""Close the f***ing programme at all costs."""

		logger.debug('Quitting game.')
		pg_quit()
		raise Exception('Game has ended.')

	def update(self, /) -> None:
		"""Update the window (called every frame)."""

		# noinspection PyTypeChecker
		self.clock.tick(DisplayConstants.FRAME_RATE)

		condition = (not pgd.get_init() or not pgd.get_surface())

		if condition or config.game.check_for_player_departure(len(Players)):
			self.quit_game()

		pgd.update()
		new_game_info, broken_connection = config.client.update()

		if broken_connection and self.window_caption is not WindowConstants.CONNECTION_BROKEN_CAPTION:
			pgd.set_caption(WindowConstants.CONNECTION_BROKEN_CAPTION)
			self.window_caption = WindowConstants.CONNECTION_BROKEN_CAPTION

		elif not config.client.connection_broken and self.window_caption is WindowConstants.CONNECTION_BROKEN_CAPTION:
			pgd.set_caption(WindowConstants.DEFAULT_WINDOW_CAPTION)
			self.window_caption = WindowConstants.DEFAULT_WINDOW_CAPTION

		if new_game_info:
			logger.debug(f'Obtained new message from Client, {new_game_info}.')

			if new_game_info != DEFAULT_NETWORK_MESSAGE:
				with config.game as g:
					g.update_from_server(new_game_info, config.playerindex)

				logger.debug('Client-side game successfully updated.')

		self.window.fill(config.GameSurf.colour)
		# Calling update() on the game_surf itself calls update() on all other surfs
		self.window.blit(*config.GameSurf.update())

		for event in pg_event_get():
			self.handle_event(event=event, event_type=event.type)

		self.display_updates_completed += 1

		if (Time := get_ticks()) > self.last_display_log + LOGGING_FREQUENCY:
			self.last_display_log = Time
			logger.debug(f'{self.display_updates_completed} display updates completed.')

		if broken_connection:
			delay(CONNECTION_BROKEN_DELAY)

	def new_window_size(
			self,
			/,
			*,
			event_key: int = 0,
			toggle_fullscreen: bool = False,
			window_dimensions: Optional[Dimensions] = None
	) -> None:

		logger.debug(f'NewWindowSize(ToggleFullscreen={toggle_fullscreen}, WindowDimensions={window_dimensions}).')

		if event_key == pgl.K_ESCAPE and not self.fullscreen:
			return None

		initialise_arg = pgl.RESIZABLE

		if toggle_fullscreen:
			self.window_dimensions = screen_x, screen_y = config.screen_size
			self.deactivate_video_resize = True

			if self.fullscreen:
				exit_toggle_amount = DisplayConstants.EXIT_FULLSCREEN_TOGGLE_AMOUNT
				window_width = screen_x - exit_toggle_amount
				window_height = screen_y - exit_toggle_amount
				self.window_dimensions = Dimensions(window_width, window_height)
				self.restart_display()
			else:
				initialise_arg = pgl.FULLSCREEN

			self.fullscreen = not self.fullscreen
		else:
			self.window_dimensions = window_dimensions

		self.initialise_window(initialise_arg)

		display.SurfaceCoordinator.new_window_size(
			window_dimensions=self.window_dimensions,
			reset_pos=(toggle_fullscreen and self.fullscreen)
		)

		for surf in (config.HandSurf, config.BoardSurf, config.TrumpCardSurf):
			surf.update_card_rects(force_update=True)

	# noinspection PyAttributeOutsideInit
	def initialise_window(self, /, flags: int) -> None:
		"""Initialise the window."""

		self.window = pgd.set_mode(self.window_dimensions, flags=flags)
		self.window.fill(config.GameSurf.colour)
		pgd.update()

	def restart_display(self, /) -> None:
		"""Restart the pygame display module; set the caption and window icon."""

		pgd.quit()
		pgd.init()
		pgd.set_caption(self.window_caption)
		pgd.set_icon(self.window_icon)

	def zoom_in(self, /) -> None:
		"""Zoom in one notch."""

		if self.fullscreen:
			return

		width, height = self.window_dimensions
		window_toggle_amount = DisplayConstants.WINDOW_RESIZE_TOGGLE_AMOUNT
		a, b = (width + window_toggle_amount), (height + window_toggle_amount)
		screen_x, screen_y = config.screen_size

		if a >= screen_x and b >= screen_y:
			self.new_window_size(toggle_fullscreen=True)
			return

		width, resize_needed1 = zoom_in_helper(
			new_var=a,
			old_var=width,
			screen_size=Dimensions(width=screen_x, height=screen_y),
			index=0
		)

		height, resize_needed2 = zoom_in_helper(
			new_var=b,
			old_var=height,
			screen_size=Dimensions(width=screen_x, height=screen_y),
			index=1
		)

		if resize_needed1 or resize_needed2:
			self.new_window_size(window_dimensions=Dimensions(width, height))

	def zoom_out(self, /) -> None:
		"""Zoom out one notch."""

		width, height = self.window_dimensions

		if width == height == DimensionConstants.MINIMUM_WINDOW_DIMENSION:
			return

		window_toggle_amount = DisplayConstants.WINDOW_RESIZE_TOGGLE_AMOUNT
		# noinspection PyTypeChecker
		a, b = (width - window_toggle_amount), (height - window_toggle_amount)

		width, resize_needed1 = zoom_out_helper(new_var=a, old_var=width)
		height, resize_needed2 = zoom_out_helper(new_var=b, old_var=height)

		if resize_needed1 or resize_needed2:
			self.new_window_size(window_dimensions=Dimensions(width, height), toggle_fullscreen=self.fullscreen)

	def video_resize_event(self, /, *, new_size: Dimensions) -> None:
		"""Respond to a pygame "video resize" event.

		Videoresize events are triggered on exiting/entering fullscreen as well as manual resizing;
		we only want our `DisplayManager.new_window_size` method to be triggered after a manual resize.
		"""

		if self.deactivate_video_resize:
			self.deactivate_video_resize = False
		else:
			self.new_window_size(window_dimensions=new_size)

	def handle_event(self, /, *, event: Event, event_type: int) -> None:
		"""Respond to a pygame event of any sort."""

		if event_type == pgl.QUIT:
			self.quit_game()

		elif event_type == pgl.KEYDOWN:
			if config.Scrollwheel.is_down:
				config.Scrollwheel.comes_up()

			elif (ev_key := event.key) in KeyConstants.WINDOW_RESIZE_KEYS:
				self.new_window_size(event_key=ev_key, toggle_fullscreen=True)

			elif control_key_down():
				try:
					self.control_key_functions[ev_key]()
				except KeyError:
					self.key_down_events(event, ev_key)

			else:
				self.key_down_events(event, ev_key)

		elif event_type == pgl.VIDEORESIZE:
			self.video_resize_event(new_size=Dimensions(*event.size))

		elif event_type == pgl.MOUSEBUTTONDOWN:
			button = event.button

			# pushing the scrollwheel down will click the scrollwheel, no matter what else is going on
			if button == 2:
				config.Scrollwheel.clicked()

			# if the scrollwheel is down, any button on the mouse being pushed will cause it to come up.
			elif config.Scrollwheel.is_down:
				config.Scrollwheel.comes_up()

			# This only applies if it ISN'T  scrollwheel press and the scrollwheel is NOT currently down.
			elif not config.input_context.fireworks_display:
				if control_key_down():
					if button == 4:
						self.zoom_in()
					elif button == 5:
						self.zoom_out()
					elif not config.client.connection_broken and button == 1 and not pg_mouse_get_pressed(5)[2]:
						config.Mouse.click = True

				elif button == 4:
					config.GameSurf.nudge_up()

				elif button == 5:
					config.GameSurf.nudge_down()

				# Whether or not clicks are needed is tested in the Gameplay Loop function
				elif not config.client.connection_broken and button == 1 and not pg_mouse_get_pressed(5)[2]:
					config.Mouse.click = True

		elif not config.input_context.fireworks_display:
			if event_type == pgl.MOUSEBUTTONUP:
				if (button := event.button) == 1 and not config.client.connection_broken:
					config.Mouse.click = False
				elif button == 2 and get_ticks() > config.Scrollwheel.original_down_time + DisplayConstants.SCROLLWHEEL_EVENT_FREQUENCY:
					config.Scrollwheel.comes_up()

			elif event_type == pgl.MOUSEMOTION and pg_mouse_get_pressed(5)[0] and pg_mouse_get_pressed(5)[2]:
				config.GameSurf.mouse_move(event.rel)

	def key_down_events(self, /, event: Event, ev_key: int) -> None:
		"""Respond to pygame events that involve the user pressing a key down."""

		if not config.input_context.fireworks_display and ev_key in KeyConstants.ARROW_KEYS:
			self.arrow_key_functions[ev_key]()

		elif not config.client.connection_broken:
			if config.input_context.game_reset and ev_key in KeyConstants.GAME_REMATCH_KEYS:
				config.game.repeat_game = True
				config.client.queue_message('@1')
			elif ev_key == pgl.K_BACKSPACE:
				config.UserInput.normal_backspace_event()
			elif ev_key == pgl.K_RETURN:
				config.UserInput.enter_event()
			else:
				config.UserInput.add_text_event(event.unicode)

	def __repr__(self) -> str:
		icon_file_path = WindowConstants.PYGAME_ICON_FILE_PATH

		return f'''Object for managing all variables related to pygame display on the client-side of the game. Current state:
-MinGameWidth: {DimensionConstants.MIN_GAME_WIDTH}
-MinGameHeight: {DimensionConstants.MIN_GAME_HEIGHT}
-DefaultMaxWidth = {DimensionConstants.DEFAULT_MAX_WIDTH}
-DefaultMaxHeight = {DimensionConstants.DEFAULT_MAX_HEIGHT}
-PygameIconFilePath: {icon_file_path} (absolute: {path.abspath(icon_file_path)}).
-fullscreen: {self.fullscreen}.
-deactivate_video_resize: {self.deactivate_video_resize}
-screen_x: {self.screen_width}.
-screen_y: {self.screen_height}.
-Fonts: {display.SurfaceCoordinator.fonts}.
-Colourscheme: [[\n\n{display.SurfaceCoordinator.colour_scheme}]].
-firework_vars: [[\n\n{self.firework_vars}]].
-WindowMargin: {display.SurfaceCoordinator.window_margin}.
-CardX: {display.SurfaceCoordinator.card_x}
-CardY: {display.SurfaceCoordinator.card_y}
-BoardCentre: {display.SurfaceCoordinator.board_centre}
-PlayStartedInputPos: {display.SurfaceCoordinator.play_started_input_pos}
-PreplayInputPos: {display.SurfaceCoordinator.preplay_input_pos}

'''
