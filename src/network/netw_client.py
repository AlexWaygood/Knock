from logging import getLogger
from queue import Queue
from time import time
from src.network.netw_abstract import Network, GetTime

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay, get_ticks as GetTicks


log = getLogger(__name__)


class Client(Network):
	__slots__ = 'addr', 'ConnectionMessage', 'SendQueue', 'ReceiveQueue', 'LastUpdate', 'ConnectionBroken', 'FrozenState'

	OnlyClient = None

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	def __new__(
			cls,
			FrozenState: bool,
			IP: str,
			port: int,
			password: str,
	):
		# noinspection PyDunderSlots,PyUnresolvedReferences
		cls.OnlyClient = super(Client, cls).__new__(cls)
		return cls.OnlyClient

	def __init__(
			self,
			FrozenState: bool,
			IP: str,
			port: int,
			password: str,
	):
		super().__init__()
		self.FrozenState = FrozenState
		self.addr = (IP, port)
		self.SendQueue = Queue()
		self.ReceiveQueue = Queue(maxsize=1)
		self.LastUpdate = 0
		self.ConnectionBroken = False

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
					from src.password_checker.pass_client import ClientPasswordChecker as PasswordChecker
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

			if (CurrentTime := time()) > Time + 5:
				print(
					"Connection failed; trying again. "
					"Check that the server script is running and you're connected to the internet."
				)

				Time = CurrentTime

	def ConnectionIsBroken(self):
		IsBroken = (self.LastUpdate < GetTicks() - 100000)

		if IsBroken is self.ConnectionBroken:
			return self.ConnectionBroken

		if IsBroken:
			print(f'Connection to the server lost at {GetTime()}!')

			if not self.FrozenState:
				log.debug('Connection to the server lost')

			self.ConnectionBroken = True
			return True

		print(f'Connection to the server restored at {GetTime()}!')

		if not self.FrozenState:
			log.debug('Connection to the server restored.')

		self.ConnectionBroken = False
		return False

	def receive(self, connecting: bool = False):
		Message = self.SubReceive(10, self.conn)
		Message = Message.split('-')[0]

		if Message[0].isdigit() and Message[1].isdigit() and not connecting:
			Message = self.SubReceive(int(Message), self.conn)

		self.LastUpdate = GetTicks()

		if not self.FrozenState:
			log.debug(f'Message received from server, {Message}.')

		self.ReceiveQueue.put(Message)

	def BlockingMessageToServer(self, message: str = '@G'):
		if message:
			self.SendQueue.put(message)

		while not self.SendQueue.empty():
			delay(100)

	# Called ClientSend to distinguish from method in parent class
	def send(self, message: str):
		if len(message) > 10:
			self.conn.sendall(f'{len(message):-<10}'.encode())
			self.conn.sendall(message.encode())
		else:
			self.conn.sendall(f'{message}:-<10'.encode())

		if not self.FrozenState:
			log.debug(f'Message sent to server, {message}.')

		self.receive()

	def CloseDown(self):
		if not self.FrozenState:
			log.debug('Attempting to close connection')

		self.send('@T')
		self.CloseConnection(self.conn)
