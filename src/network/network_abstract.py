"""

Two classes that have to do with communications between the server and clients...
...plus a one-line function for returning the current time in a fixed format.

"""

from typing import Any
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
from datetime import datetime


DEFAULT_TINY_MESSAGE_SIZE = 10
MIN_RECV_BYTES = 8192


def GetTime() -> str:
	"""Function to get the time in a fixed format"""
	return datetime.now().strftime("%H:%M:%S")


def PadMessage(Message: Any) -> str:
	return f'{Message:-<{DEFAULT_TINY_MESSAGE_SIZE}}'


class Network:
	"""Class object for encoding communication protocols between the server and client."""
	__slots__ = 'conn'

	DefaultTinyMessageSize = DEFAULT_TINY_MESSAGE_SIZE

	def __init__(self, *args, **kwargs) -> None:
		self.conn = socket(AF_INET, SOCK_STREAM)

	@staticmethod
	def SubReceive(
			AmountToReceive: int,
			conn: socket
	) -> bytes:

		response = []

		while AmountToReceive > 0:
			chunk = (conn.recv(min(MIN_RECV_BYTES, AmountToReceive)))
			AmountToReceive -= len(chunk)
			response.append(chunk)

		return b''.join(response)

	@staticmethod
	def CloseConnection(conn: socket) -> None:
		conn.shutdown(SHUT_RDWR)
		conn.close()

	@staticmethod
	def send(
			message: str,
	        conn: socket
	) -> None:

		# Create a header telling the other computer the size of the data we want to send.
		# Turn the header into a fixed-length message using f-string left-alignment, encode it, send it.
		# Then send the main message itself.
		if len(message) > DEFAULT_TINY_MESSAGE_SIZE:
			conn.sendall(PadMessage(len(message)).encode())
			conn.sendall(message.encode())
		else:
			conn.sendall(PadMessage(message).encode())
