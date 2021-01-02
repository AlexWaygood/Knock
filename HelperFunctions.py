"""A smattering of short functions (and one variable) to make the script cleaner in various other files."""

from ipaddress import ip_address
import socket
from itertools import groupby
from datetime import datetime
from string import ascii_letters, digits, punctuation


PrintableCharacters = ''.join((digits, ascii_letters, punctuation))


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
