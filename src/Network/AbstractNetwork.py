"""

Two classes that have to do with communications between the server and clients...
...plus a one-line function for returning the current time in a fixed format.

"""

import socket
from datetime import datetime


def GetTime():
	"""Function to get the time in a fixed format"""

	return datetime.now().strftime("%H:%M:%S")


class Network:
	"""Class object for encoding communication protocols between the server and client."""
	__slots__ = 'conn'

	def __init__(self, *args, **kwargs):
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	@staticmethod
	def send(message, conn):
		"""
		@type message: str
		@type conn: socket.socket
		"""

		# Create a header telling the other computer the size of the data we want to send.
		# Turn the header into a fixed-length message using f-string left-alignment, encode it, send it.
		# Then send the main message itself.
		print(f'Line 35 of Network script: message1 is {len(message):-<10}')
		print(f'Line 36 of Network script: message is {message}')
		if len(message) > 10:
			conn.sendall(f'{len(message):-<10}'.encode())
			conn.sendall(message.encode())
		else:
			conn.sendall(f'{message:-<10}'.encode())

	def receive(self, conn: socket.socket, connecting=False):
		print('Line 41 of AbstractNetworkClass')
		Message = self.SubReceive(10, conn)
		print(f'Message received is {Message}.')
		Message = Message.split('-')[0]
		print(f'Line 45: Message is now {Message}')

		if Message[0].isdigit() and Message[1].isdigit() and not connecting:
			Message = self.SubReceive(int(Message), conn)

		return Message

	@staticmethod
	def SubReceive(AmountToReceive, conn):
		"""
		@type AmountToReceive: int
		@type conn: socket.socket
		"""

		response = []

		while AmountToReceive > 0:
			chunk = (conn.recv(min(8192, AmountToReceive)))
			AmountToReceive -= len(chunk)
			response.append(chunk)

		return b''.join(response).decode()

	@staticmethod
	def CloseConnection(conn: socket.socket):
		conn.shutdown(socket.SHUT_RDWR)
		conn.close()
