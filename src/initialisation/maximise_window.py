import os, ctypes

from subprocess import check_call
from ctypes import wintypes
from msvcrt import get_osfhandle


MAX_TERMINAL_HEIGHT = 200


def MaximiseWindow() -> None:
	# Maximise the console window
	kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
	user32 = ctypes.WinDLL('user32', use_last_error=True)

	SW_MAXIMIZE = 3

	kernel32.GetConsoleWindow.restype = wintypes.HWND
	# noinspection PyUnresolvedReferences,PyProtectedMember
	kernel32.GetLargestConsoleWindowSize.restype = wintypes._COORD
	kernel32.GetLargestConsoleWindowSize.argtypes = (wintypes.HANDLE,)
	user32.ShowWindow.argtypes = (wintypes.HWND, ctypes.c_int)

	fd = os.open('CONOUT$', os.O_RDWR)

	try:
		hCon = get_osfhandle(fd)
		max_size = kernel32.GetLargestConsoleWindowSize(hCon)
		if max_size.X == 0 and max_size.Y == 0:
			raise ctypes.WinError(ctypes.get_last_error())
	finally:
		os.close(fd)

	cols = max_size.X
	hWnd = kernel32.GetConsoleWindow()

	if cols and hWnd:
		check_call('mode.com con cols={} lines={}'.format(cols, max(MAX_TERMINAL_HEIGHT, max_size.Y)))
		user32.ShowWindow(hWnd, SW_MAXIMIZE)

	# Console window now maximised.
