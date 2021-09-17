"""A class representing a network client."""

from __future__ import annotations

from typing import Union, NamedTuple, Optional
from collections import deque
from logging import getLogger
from time import time

from src.network import Network, get_time


CONNECTION_ERROR_MESSAGE_INTERVAL = 5
PING_INTERVAL = 5
CLIENT_DEFAULT_MESSAGE = 'ping'
MESSAGE_TO_TERMINATE = '@T'
logger = getLogger(__name__)


class NetworkInfoParcel(NamedTuple):
	"""A two-item tuple containing the latest message from the server, and whether the connection is still alive."""
	msg_from_server: Optional[str]
	connection_broken: bool


class Client(Network):
	"""A network client.

	The SOLE purpose of this class is to send and receive messages to the network server.

	This class knows NOTHING about how to interpret these messages
	with respect to updating the state of the tournament or game currently in progress.
	"""

	__slots__ = {
		'addr': 'The (IP, port) connection address of the server.',
		'send_queue': 'A deque of messages to be sent to the server.',
		'receive_queue': 'A queue of messages received from the server, of maximum length 1.',
		'last_update_time': 'The time at which the last update from the server was received.'
	}

	def __init__(self, ip_addr: str, port: int, password: str, send_queue_len: int, receive_queue_len: int) -> None:
		super().__init__()
		self.addr = (ip_addr, port)
		self.send_queue = deque(maxlen=send_queue_len)
		self.receive_queue = deque(maxlen=receive_queue_len)
		self.last_update_time = time()

		print(f'Starting attempt to connect at {get_time()}, loading data...')

		error_tuple = (
			"'NoneType' object is not subscriptable",
			'[WinError 10061] No connection could be made because the target machine actively refused it'
		)

		start_time = time()

		while True:
			try:
				self.conn.connect(self.addr)

				if password:
					from src.password_checker.password_client import ClientPasswordChecker as PasswordChecker
					# Sends the password to the server in __init__()
					PasswordChecker(self, self.conn, password)

				print(f'Connected at {get_time()}.')
				self.receive(connecting=True)
				break

			except (TypeError, ConnectionRefusedError) as e:
				if str(e) in error_tuple:
					print('Initial connection failed; has the server been initialised?')
					print('Further attempts will be made to connect until a connection is successful.')
					continue
				raise e

			except OSError as e:
				if str(e) == '[WinError 10051] A socket operation was attempted to an unreachable network':
					print("OSError. Check you're connected to the internet?")
					raise e

			if (current_time := time()) > start_time + CONNECTION_ERROR_MESSAGE_INTERVAL:
				print(
					"Connection failed; trying again. "
					"Check that the server script is running and you're connected to the internet."
				)

				start_time = current_time

	def update(self, /) -> NetworkInfoParcel:
		"""Return the latest message from the server, and whether or not the connection is still alive."""
		return NetworkInfoParcel(self.latest_message_from_server, self.connection_broken)

	def receive(self, /, *, connecting: bool = False) -> None:
		"""Receive a message from the server, and add it to the queue of received messages."""

		message = self.sub_receive(self.default_tiny_message_size, self.conn).decode()
		message = message.split('-')[0]

		if message[0].isdigit() and message[1].isdigit() and not connecting:
			message = self.sub_receive(int(message), self.conn)

		self.last_update = time()
		logger.debug(f'Message received from server, {message}.')
		self.receive_queue.append(message)

	def client_send(self, message: str) -> None:
		"""Send a message to the server."""

		self.send(message, self.conn)
		logger.debug(f'Message sent to server, {message}.')
		self.receive()

	def queue_message(self, message: str, /) -> None:
		"""Queue a message to be sent to the server."""
		self.send_queue.append(message)

	@property
	def latest_message_from_server(self, /) -> Union[str, None]:
		"""Get the latest message from the server, if there is one."""

		try:
			return self.receive_queue.popleft()
		except KeyError:
			return None

	@property
	def connection_broken(self, /) -> bool:
		"""Detect whether the connection is broken."""
		is_broken = self.last_update_time < (time() - 10)

		if is_broken:
			logger.debug('Connection to the server lost')

		return is_broken

	def close_down(self, /) -> None:
		"""Close the network connection."""

		logger.debug('Attempting to close connection')
		self.client_send(MESSAGE_TO_TERMINATE)
		self.close_connection(self.conn)
