"""Set pygame blocked events."""


def set_pygame_blocked_events() -> None:
	"""Set pygame blocked events."""

	import pygame as pg

	pg.event.set_blocked((
		pg.AUDIODEVICEADDED,
		pg.AUDIODEVICEREMOVED,
		pg.FINGERMOTION,
		pg.FINGERUP,
		pg.FINGERDOWN,
		pg.MOUSEWHEEL,
		pg.MULTIGESTURE,
		pg.TEXTINPUT,
		pg.TEXTEDITING,
		pg.WINDOWRESTORED,
		pg.WINDOWCLOSE,
		pg.WINDOWENTER,
		pg.WINDOWEXPOSED,
		pg.WINDOWHIDDEN,
		pg.WINDOWFOCUSGAINED,
		pg.WINDOWHITTEST,
		pg.WINDOWLEAVE,
		pg.WINDOWMOVED,
		pg.WINDOWRESIZED,
		pg.WINDOWSHOWN,
		pg.WINDOWFOCUSLOST,
		pg.WINDOWMAXIMIZED,
		pg.WINDOWMINIMIZED,
		pg.WINDOWSIZECHANGED,
		pg.WINDOWTAKEFOCUS,
		pg.ACTIVEEVENT,
		pg.USEREVENT,
		pg.VIDEOEXPOSE,
	))


def test_set_blocked_events() -> None:
	"""Test if `set_blocked_events()` works."""

	import pygame as pg
	pg.init()
	pg.display.init()
	set_pygame_blocked_events()
	assert pg.event.get_blocked(pg.WINDOWMAXIMIZED)
	assert pg.event.get_blocked((pg.AUDIODEVICEADDED, pg.WINDOWMOVED))
