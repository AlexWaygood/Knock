"""A smattering of short functions (and one variable) to make the script cleaner in various other files."""

from ipaddress import ip_address
import socket
from itertools import groupby
from datetime import datetime
from string import ascii_letters, digits, punctuation
from fractions import Fraction


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


def GameStarted(x, y):
	"""y value is deliberately not used due to the specific use of this function"""

	return not x.StartPlay


def AllBid(x, y):
	"""y value is deliberately not used due to the specific use of this function"""
	return not x.gameplayers.AllBid()


def CalculateDimensions1(NewGameSurfaceDimensions, CurrentCardDimensions=(691, 1056)):
	"""This function is designed to be used both at the beginning of the game and midway through the game"""

	# Calculate the required size of the card images, based on various ratios of surfaces that will appear on the screen.
	# Lots of "magic numbers" here, based purely on the principle of "keep the proportions that look good on my laptop".

	GameX, GameY = NewGameSurfaceDimensions
	WindowMargin = int(GameX * Fraction(15, 683))
	ImpliedCardHeight = min(((GameY // Fraction(768, 150)) - WindowMargin), (GameY // 5.5))
	ImpliedCardWidth = ImpliedCardHeight * Fraction(*CurrentCardDimensions)
	NewCardDimensions = (ImpliedCardWidth.__ceil__(), ImpliedCardHeight.__ceil__())
	RequiredResizeRatio = CurrentCardDimensions[1] / ImpliedCardHeight

	return WindowMargin, NewCardDimensions, RequiredResizeRatio
