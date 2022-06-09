"""

Two classes that have to do with communications between the server and clients...
...plus a one-line function for returning the current time in a fixed format.

"""

from typing import Any
from socket import socket, AF_INET, SOCK_STREAM, SHUT_RDWR
import time


DEFAULT_TINY_MESSAGE_SIZE = 10
MIN_RECV_BYTES = 8192


def get_time() -> str:
	"""Function to get the time in a fixed format"""
	return time.strftime('%H:%M:%S')


def pad_message(message: Any) -> str:
	"""Pad a message so that it is the minimum length required before sending it across the network.

	Parameters
	----------
	message: Any
		The message to be padded.
		Since any type can be converted into a string when passed into an f-string, this annotation is `Any`.

	Returns
	-------
	str: The padded message.
	"""

	return f'{message:-<{DEFAULT_TINY_MESSAGE_SIZE}}'


class Network:
	"""Abstract base class encoding communication protocols between the server and client."""

	__slots__ = {'conn': 'A socket connection'}
	default_tiny_message_size = DEFAULT_TINY_MESSAGE_SIZE

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		self.conn = socket(AF_INET, SOCK_STREAM)

	@staticmethod
	def sub_receive(amount_to_receive: int, conn: socket) -> bytes:
		response = []

		while amount_to_receive > 0:
			chunk = (conn.recv(min(MIN_RECV_BYTES, amount_to_receive)))
			amount_to_receive -= len(chunk)
			response.append(chunk)

		return b''.join(response)

	@staticmethod
	def close_connection(conn: socket, /) -> None:
		"""Close a network connection.

		Parameters
		----------
		conn: socket
			The socket connection which is to be closed.

		Returns
		-------
		None
		"""

		conn.shutdown(SHUT_RDWR)
		conn.close()

	@staticmethod
	def send(message: str, conn: socket) -> None:
		"""Send a message across the network.

		Parameters
		----------
		message: str
			The message to be sent.
		conn: socket
			The connection over which the message is to be sent.

		Returns
		-------
		None
		"""

		# Create a header telling the other computer the size of the data we want to send.
		# Turn the header into a fixed-length message using f-string left-alignment, encode it, send it.
		# Then send the main message itself.
		if len(message) > DEFAULT_TINY_MESSAGE_SIZE:
			conn.sendall(pad_message(len(message)).encode())
			conn.sendall(message.encode())
		else:
			conn.sendall(pad_message(message).encode())
