"""

Two classes that have to do with communications between the server and clients...
...plus a one-line function for returning the current time in a fixed format.

"""

from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from datetime import datetime


def GetTime():
	"""Function to get the time in a fixed format"""
	return datetime.now().strftime("%H:%M:%S")


class Network:
	"""Class object for encoding communication protocols between the server and client."""
	__slots__ = 'conn'

	def __init__(self, *args, **kwargs):
		self.conn = socket(AF_INET, SOCK_STREAM)

	@staticmethod
	def SubReceive(AmountToReceive: int,
	               conn: socket):

		response = []

		while AmountToReceive > 0:
			chunk = (conn.recv(min(8192, AmountToReceive)))
			AmountToReceive -= len(chunk)
			response.append(chunk)

		return b''.join(response).decode()

	@staticmethod
	def CloseConnection(conn: socket):
		conn.shutdown(SHUT_RDWR)
		conn.close()
