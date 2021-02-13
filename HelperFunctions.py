"""A smattering of short functions (and one variable) to make the script cleaner in various other files."""

from ipaddress import ip_address
import socket
from itertools import groupby
from datetime import datetime
from string import ascii_letters, digits, punctuation
from fractions import Fraction
from math import ceil
from collections import namedtuple


PrintableCharacters = ''.join((digits, ascii_letters, punctuation))
PrintableCharactersPlusSpace = PrintableCharacters + ' '


def GetTime():
	"""Function to get the time in a fixed format"""

	return datetime.now().strftime("%H:%M:%S")


def IPValidation(InputText):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = socket.gethostbyname(InputText)
		ip_address(address)

	return InputText


def AllEqual(Iterable):
	"""Does what it says on the tin"""

	g = groupby(Iterable)
	return next(g, True) and not next(g, False)


def GetDimensions1(NewGameSurfDimensions, CurrentCardDimensions=(691, 1056)):
	"""This function is designed to be used both at the beginning of the game and midway through the game"""

	# Calculate the required size of the card images, based on various ratios of surfaces that will appear on the screen.
	# Lots of "magic numbers" here, based purely on the principle of "keep the proportions that look good on my laptop".

	GameX, GameY = NewGameSurfDimensions
	WindowMargin = int(GameX * Fraction(15, 683))
	ImpliedCardHeight = min(((GameY // Fraction(768, 150)) - WindowMargin), (GameY // 5.5))
	ImpliedCardWidth = ImpliedCardHeight * Fraction(*CurrentCardDimensions)
	NewCardDimensions = (ceil(ImpliedCardWidth), ceil(ImpliedCardHeight))
	RequiredResizeRatio = CurrentCardDimensions[1] / ImpliedCardHeight
	return WindowMargin, NewCardDimensions, RequiredResizeRatio


def ResizeHelper(var1, var2, ScreenSize, i):
	var1 = ScreenSize[i] if var1 > ScreenSize[i] else var1
	var1 = 10 if var1 < 10 else var1
	ResizeNeeded = (var1 != var2)
	var2 = var1
	return var2, ResizeNeeded


Action = namedtuple('Action', ['Type', 'args'])


class OpenableObject(object):
	__slots__ = 'value'

	def __init__(self):
		self.value = False

	def __enter__(self):
		self.value = True
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.value = False
		return self

	def __bool__(self):
		return self.value


class MessageHolder(object):
	__slots__ = 'm', 'font'

	def __init__(self):
		self.m = ''

	def __call__(self, m, font):
		self.m = m
		self.font = font
		return self

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.m = ''
		return self

	def __bool__(self):
		return bool(self.m)
