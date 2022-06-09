import socket
import time
from collections import deque
from functools import partial
from logging import getLogger
from enum import Enum
from select import select
from abc import ABCMeta, abstractmethod
from typing import Optional, Any, Iterator, TypeVar, Final, Union, NamedTuple, NoReturn, Generic
from src import DocumentedPlaceholders, abstract_classmethod_property, classmethod_property


logger = getLogger(__name__)


def print_and_log(message: str, /) -> None:
	"""Print a message to the screen and log it to the logging file."""
	print(message)
	logger.debug(message)


get_time = partial(time.strftime, '%H:%M:%S')
get_time.__doc__ = 'Function to get the current time in a fixed format.'


class AbstractMessage:
	"""Base class for `SendableMessage` and `MessageBeingReceived`."""
	MINIMUM_MESSAGE_SIZE: Final = 10
	PADDING_CHARACTER: Final = '-'
	PING: Final = 'PING'


# noinspection PyTypeChecker
S = TypeVar('S', bound='SendableMessage')


class SendableMessage(AbstractMessage):
	"""Object representing a message to be sent to the other partner in the connection."""

	@classmethod
	def _pad_message(cls, message: Any, /) -> str:
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

		return f'{message:{cls.PADDING_CHARACTER}<{cls.MINIMUM_MESSAGE_SIZE}}'

	@classmethod
	def _prepare_message_for_sending(cls, message: str, /) -> bytes:
		if len(message) <= cls.MINIMUM_MESSAGE_SIZE:
			return cls._pad_message(message).encode()
		return f'{cls._pad_message(len(message))}{message}'.encode()

	def __init__(self, message: str, /) -> None:
		self.bytes_to_be_sent = self._prepare_message_for_sending(message)

	@classmethod
	def ping_message(cls: type[S], /) -> S:
		"""Send a ping."""
		return cls(cls.PING)

	def update_after_bytes_sent(self, /, *, num_bytes_sent: int) -> None:
		"""Update internal state after a portion of the message was sent over the network."""
		self.bytes_to_be_sent = self.bytes_to_be_sent[num_bytes_sent:]

	def __bool__(self, /) -> bool:
		return bool(self.bytes_to_be_sent)

	def __bytes__(self, /) -> bytes:
		return self.bytes_to_be_sent

	def __iter__(self, /) -> Iterator[str]:
		return iter(self.bytes_to_be_sent)


K = TypeVar('K')


class MessageHeaderKind(Enum):
	"""There are two kinds of message headers: complete messages, and headers indicating length of a full message."""

	# We have to use functools.partial here or these functions will be converted into Enum methods rather than members.

	MESSAGE_LENGTH_INDICATOR = partial(lambda message_header: message_header[:2].isdigit())
	PING = partial(AbstractMessage.PING.__eq__)
	COMPLETE_MESSAGE = partial(lambda message_header: True)

	def validates(self, message_header: str) -> bool:
		"""Validate whether a message header is of this kind or not."""
		return self.value(message_header)

	@classmethod
	def identify_kind_of(cls: type[K], message_header: str, /) -> K:
		"""Given a decoded message header, identify what kind of header it is."""
		return next(header_kind for header_kind in cls if header_kind.validates(message_header))


class MessageBeingReceived(AbstractMessage):
	"""Object representing a message being received from the other party in the connection."""

	def __init__(self, /) -> None:
		self.amount_still_to_come = self.MINIMUM_MESSAGE_SIZE
		self.received_chunks: list[bytes] = []
		self.size_known = False

	def _decode_message_header(self, header: bytes, /) -> str:
		"""Remove the padding from a received header and decode it from bytes to string."""
		return header.decode().split(self.PADDING_CHARACTER)[0]

	def _process_ping_from_server(self, /) -> None:
		self.amount_still_to_come = self.MINIMUM_MESSAGE_SIZE
		self.received_chunks.clear()

	def _process_message_length_indicator(self, /, *, message_header: str) -> None:
		self.amount_still_to_come = int(message_header)
		self.received_chunks.clear()
		self.size_known = True

	def add_chunk(self, chunk: bytes, /) -> None:
		"""Add a chunk to the list of received chunks, calculate whether there is more to be received or not."""

		amount_still_to_come = self.amount_still_to_come - len(chunk)

		if self.size_known:
			if amount_still_to_come >= 0:
				self.received_chunks.append(chunk)
				self.amount_still_to_come = amount_still_to_come
				return None

			this_message, next_message = chunk[:amount_still_to_come], chunk[amount_still_to_come:]
			self.received_chunks.append(this_message)
			self.amount_still_to_come = 0
			return next_message

		if amount_still_to_come > 0:
			self.received_chunks.append(chunk)
			self.amount_still_to_come = amount_still_to_come
			return None

		if amount_still_to_come:
			this_message, next_message = chunk[:amount_still_to_come], chunk[amount_still_to_come:]
		else:
			this_message, next_message = chunk, None

		self.received_chunks.append(this_message)
		joined_header = b''.join(self.received_chunks)
		message_header = self._decode_message_header(joined_header)
		message_header_kind = MessageHeaderKind.identify_kind_of(message_header)

		if message_header_kind is MessageHeaderKind.PING:
			self._process_ping_from_server()
		elif message_header_kind is MessageHeaderKind.MESSAGE_LENGTH_INDICATOR:
			self._process_message_length_indicator(message_header=message_header)

	@property
	def full_message_received(self, /) -> bool:
		"""Return `True` if the message has finished being received, else `False`."""
		return not self.amount_still_to_come

	def as_str(self, /) -> str:
		"""Return the fully received message as a string."""
		if not self.full_message_received:
			raise RuntimeError('The full message has not yet been received!')
		return b''.join(self.received_chunks).decode()


class ConnectionAddress(NamedTuple):
	"""A tuple consisting of the IP address of the other party, and the port."""
	ip_address: str
	port: int


class ConnectionStatusLogger:
	"""Handler for monitoring the status of a connection and """

	MAX_SECONDS_BETWEEN_MESSAGES: Final = 10
	LOGGING_INTERVAL: Final = 1

	# noinspection PyPep8Naming,PyMissingOrEmptyDocstring
	class NO_LOGGING_REQUIRED(DocumentedPlaceholders): pass

	def __init__(self, /, *, connection_address: ConnectionAddress) -> None:
		self.connection_address = connection_address
		self.time_last_message_received = 0
		self.last_connection_status_log_time = 0
		self.connection_was_broken_at_last_log = False

	@property
	def logging_update_required(self, /) -> bool:
		"""Determine whether enough time has elapsed that we need to log the connection status to the file."""
		return time.time() > self.last_connection_status_log_time + self.LOGGING_INTERVAL

	@property
	def connection_broken(self) -> bool:
		"""Determine whether the connection is alive or not."""
		return time.time() < self.time_last_message_received + self.MAX_SECONDS_BETWEEN_MESSAGES

	@property
	def _broken_connection_message(self, /) -> str:
		"""Get the message we log to the file if the connection is broken (logged repeatedly)."""
		return f'Connection to {self.connection_address} broken at {get_time()}'

	@property
	def _connection_restored_message(self, /) -> str:
		"""Get the message we log to the file if the connection has just been restored (logged once)."""
		return f'Connection to {self.connection_address} restored at {get_time()}'

	def _get_connection_status(self, /) -> Union[str, type[NO_LOGGING_REQUIRED]]:
		"""Determine the message required to be logged to the file, if one needs to be logged to the file."""

		if self.connection_was_broken_at_last_log:
			if self.connection_broken:
				return self._broken_connection_message
			self.connection_was_broken_at_last_log = False
			return self._connection_restored_message
		if self.connection_broken:
			self.connection_was_broken_at_last_log = True
			return self._broken_connection_message
		return self.NO_LOGGING_REQUIRED

	def update(self, /) -> None:
		"""Update the time the last message was received and log the connection status to a file, if necessary."""
		self.time_last_message_received = time.time()

		if self.logging_update_required:
			if (connection_status := self._get_connection_status()) is not self.NO_LOGGING_REQUIRED:
				logger.debug(connection_status)


# noinspection PyTypeChecker
C = TypeVar('C', bound='Connection')


# noinspection PyPep8Naming,PyMethodParameters
class Connection(metaclass=ABCMeta):
	"""A network connection that only knows how to receive and send strings.

	A client has ONE connection,
	a server has MANY connections,
	but they are instances of the SAME `Connection` class.
	"""

	received_messages: deque[str]
	send_queue: deque[SendableMessage]

	@abstract_classmethod_property
	def MAX_BYTES_PER_RECEIVED_MESSAGE(cls, /) -> int:
		"""Subclasses need to define this on the class level."""

	@abstract_classmethod_property
	def SERVER_SEND_QUEUE_LEN(cls, /) -> Optional[int]:
		"""Subclasses need to define this on the class level."""

	@classmethod_property
	def CLIENT_RECEIVE_QUEUE_LEN(cls, /) -> Optional[int]:
		"""The length of the client connection's receive queue should always be the same as the server's send queue."""
		# noinspection PyTypeChecker
		return cls.SERVER_SEND_QUEUE_LEN

	# noinspection PyPep8Naming
	@abstract_classmethod_property
	def SERVER_RECEIVE_QUEUE_LEN(cls, /) -> Optional[int]:
		"""Subclasses need to define this on the class level."""

	@classmethod_property
	def CLIENT_SEND_QUEUE_LEN(cls, /) -> Optional[int]:
		"""The length of the client connection's send queue should always be the same as the server's receive queue."""
		return cls.SERVER_RECEIVE_QUEUE_LEN

	@staticmethod
	def make_socket_connection() -> socket:
		"""Make a new socket object."""
		return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	def __init__(
			self,
			/,
			*,
			connection: socket.socket,
			connection_address: ConnectionAddress,
			received_message_queue_len: Optional[int],
			send_message_queue_len: Optional[int]
	):
		self.received_messages = deque(maxlen=received_message_queue_len)
		self.send_queue = deque(maxlen=send_message_queue_len)
		self.message_being_received = MessageBeingReceived()
		self.socket = connection
		self.connection_address = connection_address
		self.status_logger = status_logger = ConnectionStatusLogger(connection_address=connection_address)
		self.update_status_logger = status_logger.update

	@classmethod
	def new_client_connection(cls: type[C], /, *, connection_address: ConnectionAddress) -> C:
		"""Make a client connection."""

		sock = cls.make_socket_connection()

		new_connection = cls(
			connection_address=connection_address,
			connection=sock,
			received_message_queue_len=cls.CLIENT_RECEIVE_QUEUE_LEN,
			send_message_queue_len=cls.CLIENT_SEND_QUEUE_LEN
		)

		sock.connect(connection_address)
		return new_connection

	@classmethod
	def new_server_connection(cls: type[C], /, *, sock: socket.socket, connection_address: ConnectionAddress) -> C:
		"""Make a server connection."""

		return cls(
			connection_address=connection_address,
			connection=sock,
			received_message_queue_len=cls.SERVER_RECEIVE_QUEUE_LEN,
			send_message_queue_len=cls.SERVER_SEND_QUEUE_LEN
		)

	def queue_message(self, message: str) -> None:
		"""Queue a message to be sent to the other partner in the connection."""
		self.send_queue.append(SendableMessage(message))

	@property
	def next_message(self, /) -> Optional[str]:
		"""Get the oldest message in the queue of received messages, or `None` if the queue is empty."""

		try:
			msg = self.received_messages.popleft()
		except IndexError:
			msg = None

		return msg

	def receive_messages(self, /) -> None:
		"""Receive messages from the other party."""

		received_bytes = self.socket.recv(self.MAX_BYTES_PER_RECEIVED_MESSAGE)
		message_being_received = self.message_being_received
		message_being_received.add_chunk(received_bytes)

		if message_being_received.full_message_received:
			self.received_messages.append(message_being_received.as_str())
			self.message_being_received = MessageBeingReceived()

	def send_messages(self, /) -> None:
		"""Send any messages that need to be sent, or a 'ping' message if there are none."""

		send_queue = self.send_queue

		if not send_queue:
			send_queue.append(SendableMessage.ping_message())

		message = send_queue[0]
		amount_sent = self.socket.send(bytes(message))
		message.update_after_bytes_sent(num_bytes_sent=amount_sent)

		if not message:
			send_queue.popleft()


class KnockConnection(Connection):
	"""Base class for all Knock network connections."""
	MAX_BYTES_PER_RECEIVED_MESSAGE = 8192
	SERVER_SEND_QUEUE_LEN = 1
	SERVER_RECEIVE_QUEUE_LEN = None


class ConnectionManager(Generic[C], metaclass=ABCMeta):
	"""A base class for managing one or more network connections."""

	@abstractmethod
	def update(self, /) -> None:
		"""Update all connections we are managing."""


class Server(ConnectionManager[C]):
	"""An abstract server."""

	connections_dict: dict[socket.socket, C]

	def __init__(self, /, *, max_connections: int, server_address: ConnectionAddress) -> None:
		self.connections_dict = {}
		self.max_connections = max_connections
		self.sock = sock = Connection.make_socket_connection()
		sock.bind(server_address)
		self.inputs = [sock]
		self.outputs = []

	def run(self, /) -> NoReturn:
		"""Run the server in an infinite loop until the end of the game."""

		print_and_log('Initialising server...')
		self.sock.listen()
		print_and_log(f'Ready to accept connections to the server (time {get_time()}).\n')

		while True:
			self.update()

	def update(self, /) -> None:
		"""Update all connections we are managing."""

		inputs, connections_dict = self.inputs, self.connections_dict
		readable, writable, exceptional = select(inputs, self.outputs, inputs, 60)

		for sock in readable:
			if sock is self.sock:
				if len(connections_dict) <= self.max_connections:
					self.connect_to_client()
			else:
				connections_dict[sock].receive_messages()

		for sock in writable:
			connections_dict[sock].send_messages()

		# Do something with exceptions

	def connect_to_client(self, /) -> None:
		"""Connect to a client."""

		new_connection, (ip, port) = self.sock.accept()

		self.connections_dict[new_connection] = self.new_connection(
			connection=new_connection,
			connection_address=ConnectionAddress(ip, port)
		)

	@staticmethod
	@abstractmethod
	def new_connection(*, connection: socket.socket, connection_address: ConnectionAddress) -> Connection:
		"""Make a new server connection"""


class Client(ConnectionManager):
	"""An abstract client."""
	def update(self, /) -> None:
		"""Update the connection to the server."""

	@staticmethod
	@abstractmethod
	def new_connection(*, connection_address: ConnectionAddress) -> Connection:
		"""Make a new client connection"""


class KnockServer(Server):
	"""A Knock server."""

	MAX_CONNECTIONS = 6
	new_connection = KnockConnection.new_server_connection

	def __init__(self, /, *, server_address: ConnectionAddress) -> None:
		super().__init__(max_connections=self.MAX_CONNECTIONS, server_address=server_address)


class KnockClient(Client):
	"""A Knock client."""
	new_connection = KnockConnection.new_client_connection
