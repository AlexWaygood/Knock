from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn
from queue import Queue
from time import time
from traceback_with_variables import printing_exc

from src.network.network_abstract import Network, GetTime
from src.misc import GetLogger

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import delay, get_ticks as GetTicks

if TYPE_CHECKING:
	from src.display.input_context import InputContext
	from src.special_knock_types import OptionalClient, ClientUpdateReturn


CONNECTION_ERROR_MESSAGE_INTERVAL = 5
PING_INTERVAL = 5
CLIENT_DEFAULT_MESSAGE = 'ping'
MESSAGE_TO_TERMINATE = '@T'


def DetectBrokenConnection(LastUpdateTime: int) -> bool:
	return LastUpdateTime < (GetTicks() - 10000)


class Client(Network):
	__slots__ = 'addr', 'ConnectionMessage', 'SendQueue', 'ReceiveQueue', 'LastUpdate', 'ConnectionBroken', 'log'

	OnlyClient: OptionalClient = None

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	def __new__(
			cls,
			FrozenState: bool,
			IP: str,
			port: int,
			password: str,
	) -> Client:

		# noinspection PyDunderSlots,PyUnresolvedReferences
		cls.OnlyClient = super(Client, cls).__new__(cls)
		return cls.OnlyClient

	def __init__(
			self,
			FrozenState: bool,
			IP: str,
			port: int,
			password: str,
	) -> NoReturn:

		super().__init__()
		self.addr = (IP, port)
		self.SendQueue = Queue()
		self.ReceiveQueue = Queue(maxsize=1)
		self.LastUpdate = 0
		self.ConnectionBroken = False
		self.log = GetLogger(FrozenState)

		print(f'Starting attempt to connect at {GetTime()}, loading data...')

		ErrorTuple = (
			"'NoneType' object is not subscriptable",
			'[WinError 10061] No connection could be made because the target machine actively refused it'
		)

		Time = time()

		while True:
			try:
				self.conn.connect(self.addr)

				if password:
					from src.password_checker.password_client import ClientPasswordChecker as PasswordChecker
					PasswordChecker(self, self.conn, password)  # Sends the password to the server in __init__()

				print(f'Connected at {GetTime()}.')
				self.receive(connecting=True)
				break

			except (TypeError, ConnectionRefusedError) as e:
				if str(e) in ErrorTuple:
					print('Initial connection failed; has the server been initialised?')
					print('Further attempts will be made to connect until a connection is successful.')
					continue
				raise e

			except OSError as e:
				if str(e) == '[WinError 10051] A socket operation was attempted to an unreachable network':
					print("OSError. Check you're connected to the internet?")
					raise e

			if (CurrentTime := time()) > Time + CONNECTION_ERROR_MESSAGE_INTERVAL:
				print(
					"Connection failed; trying again. "
					"Check that the server script is running and you're connected to the internet."
				)

				Time = CurrentTime

	def Update(self) -> ClientUpdateReturn:
		if (IsBroken := (DetectBrokenConnection(self.LastUpdate))) is self.ConnectionBroken:
			pass

		elif IsBroken:
			print(f'Connection to the server lost at {GetTime()}!')
			self.log.debug('Connection to the server lost')
			self.ConnectionBroken = True

		else:
			print(f'Connection to the server restored at {GetTime()}!')
			self.log.debug('Connection to the server restored.')
			self.ConnectionBroken = False

		return (None if self.ReceiveQueue.empty() else self.ReceiveQueue.get()), self.ConnectionBroken

	def receive(self, connecting: bool = False) -> None:
		Message = self.SubReceive(self.DefaultTinyMessageSize, self.conn).decode()
		Message = Message.split('-')[0]

		if Message[0].isdigit() and Message[1].isdigit() and not connecting:
			Message = self.SubReceive(int(Message), self.conn)

		self.LastUpdate = GetTicks()
		self.log.debug(f'Message received from server, {Message}.')
		self.ReceiveQueue.put(Message)

	def BlockingMessageToServer(
			self,
			message: str = CLIENT_DEFAULT_MESSAGE
	) -> None:

		if message:
			self.SendQueue.put(message)

		while not self.SendQueue.empty():
			delay(100)

	def ClientSend(self, message: str) -> None:
		self.send(message, self.conn)
		self.log.debug(f'Message sent to server, {message}.')
		self.receive()

	def UpdateLoop(self, context: InputContext) -> NoReturn:
		with printing_exc():
			while True:
				delay(100)

				if self.SendQueue.empty():
					if context.GameUpdatesNeeded or self.LastUpdate < (time() - PING_INTERVAL):
						self.ClientSend(CLIENT_DEFAULT_MESSAGE)
					continue

				self.ClientSend(self.SendQueue.get())

	def QueueMessage(self, message: str) -> None:
		self.SendQueue.put(message)

	def CloseDown(self) -> None:
		self.log.debug('Attempting to close connection')
		self.ClientSend(MESSAGE_TO_TERMINATE)
		self.CloseConnection(self.conn)
