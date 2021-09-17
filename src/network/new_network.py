import socket
from collections import deque
from functools import cache
from time import time
from enum import Enum, auto
from typing import Optional, Any, Iterator, TypeVar


class Message:
	"""Base class for `SendableMessage` and `MessageBeingReceived`."""
	MINIMUM_MESSAGE_SIZE = 10
	PADDING_CHARACTER = '-'


class SendableMessage(Message):
	"""Object representing a message to be sent to the other partner in the connection."""

	@classmethod
	def _pad_message(cls, message: Any) -> str:
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
	def _prepare_message_for_sending(cls, message: str) -> bytes:
		if len(message) <= cls.MINIMUM_MESSAGE_SIZE:
			return cls._pad_message(message).encode()
		return f'{cls._pad_message(len(message))}{message}'.encode()

	def __init__(self, message: str):
		self.bytes_to_be_sent = self._prepare_message_for_sending(message)

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

	COMPLETE_MESSAGE = auto()
	MESSAGE_LENGTH_INDICATOR = auto()

	@classmethod
	def identify_kind_of(cls: type[K], header: str) -> K:
		"""Identify whether a header is a full_message_received message or an indicator of the length of a full message."""

		first, second = header[:2]
		return cls.MESSAGE_LENGTH_INDICATOR if (first.isdigit() and second.isdigit()) else cls.COMPLETE_MESSAGE


class MessageBeingReceived(Message):
	"""Object representing a message being received from the other party in the connection."""

	def __init__(self) -> None:
		self.amount_still_to_come = self.MINIMUM_MESSAGE_SIZE
		self.received_chunks: list[bytes] = []
		self.size_known = False

	def _decode_message_header(self, header: bytes) -> str:
		"""Remove the padding from a received header and decode it from bytes to string."""
		return header.decode().split(self.PADDING_CHARACTER)[0]

	def add_chunk(self, chunk: bytes) -> None:
		self.received_chunks.append(chunk)
		amount_still_to_come = self.amount_still_to_come - len(chunk)

		if amount_still_to_come or self.size_known:
			self.amount_still_to_come = amount_still_to_come
		else:
			joined_header = b''.join(self.received_chunks)
			message_header = self._decode_message_header(joined_header)
			message_header_kind = MessageHeaderKind.identify_kind_of(message_header)
			if message_header_kind is MessageHeaderKind.MESSAGE_LENGTH_INDICATOR:
				self.amount_still_to_come = int(message_header)
				self.received_chunks.clear()
				self.size_known = True

	@property
	def full_message_received(self) -> bool:
		"""Return `True` if the message has finished being received, else `False`."""
		return not self.amount_still_to_come

	def __str__(self) -> str:
		if not self.full_message_received:
			raise RuntimeError('The full message has not yet been received!')
		return b''.join(self.received_chunks).decode()


class Connection:
	"""A network connection that only knows how to receive and send strings."""

	received_messages: deque[str]
	send_queue: deque[SendableMessage]

	PING = 'PING'
	MAX_BYTES_PER_RECEIVED_MESSAGE = 8192
	MAX_SECONDS_BETWEEN_MESSAGES = 10

	def __init__(
			self,
			/,
			*,
			ip_address: str,
			port: int,
			received_message_queue_len: int,
			send_message_queue_len: int
	):
		self.ip_address_of_other = ip_address
		self.port = port
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.received_messages = deque(maxlen=received_message_queue_len)
		self.send_queue = deque(maxlen=send_message_queue_len)
		self.message_being_received = MessageBeingReceived()
		self.last_update_time = 0

	def connect_to_other(self) -> None:
		"""Connect to the other party."""
		self.socket.connect((self.ip_address_of_other, self.port))
		self.last_update_time = time()

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

	@property
	def connection_broken(self) -> bool:
		"""Determine whether the connection is alive or not."""
		return time()

	def receive_messages(self, /) -> None:
		received_bytes = self.socket.recv(self.MAX_BYTES_PER_RECEIVED_MESSAGE)
		message_being_received = self.message_being_received
		message_being_received.add_chunk(received_bytes)

		if message_being_received.full_message_received:
			self.received_messages.append(str(message_being_received))
			self.message_being_received = MessageBeingReceived()

	def send_messages(self, /) -> None:
		send_queue = self.send_queue

		if not send_queue:
			send_queue.append(SendableMessage(self.PING))

		message = send_queue[0]
		amount_sent = self.socket.send(bytes(message))
		message.update_after_bytes_sent(num_bytes_sent=amount_sent)

		if not message:
			send_queue.popleft()

	def update(self, /) -> None:
		self.receive_messages()
		self.send_messages()
