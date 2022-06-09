"""A single function to maximise the terminal window."""

MAX_TERMINAL_HEIGHT = 200
SW_MAXIMIZE = 3


def maximise_window() -> None:
	"""Maximise the console window.

	Credit for this function goes to Eryk Sun: https://stackoverflow.com/a/43959471/13990016.
	In his Stack Overflow answer in 2017, Sun said:

		Here's a function to maximize the current console window.
		It uses ctypes to call WinAPI functions.
		First it calls GetLargestConsoleWindowSize in order to figure how big it can make the window.
		To do the work of resizing the screen buffer, it simply calls mode.com via subprocess.check_call.
		Finally, it gets the console window handle via GetConsoleWindow and calls ShowWindow to maximize it.
	"""

	import os
	import ctypes

	from subprocess import check_call
	from ctypes import wintypes
	from msvcrt import get_osfhandle

	kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
	user32 = ctypes.WinDLL('user32', use_last_error=True)

	kernel32.GetConsoleWindow.restype = wintypes.HWND
	# noinspection PyUnresolvedReferences,PyProtectedMember
	kernel32.GetLargestConsoleWindowSize.restype = wintypes._COORD
	kernel32.GetLargestConsoleWindowSize.argtypes = (wintypes.HANDLE,)
	user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)

	fd = os.open('CONOUT$', os.O_RDWR)

	try:
		h_con = get_osfhandle(fd)
		max_size = kernel32.GetLargestConsoleWindowSize(h_con)
		if max_size.X == 0 and max_size.Y == 0:
			raise ctypes.WinError(ctypes.get_last_error())
	finally:
		os.close(fd)

	cols = max_size.X
	h_wnd = kernel32.GetConsoleWindow()

	if cols and h_wnd:
		check_call('mode.com con cols={} lines={}'.format(cols, max(MAX_TERMINAL_HEIGHT, max_size.Y)))
		user32.ShowWindow(h_wnd, SW_MAXIMIZE)
