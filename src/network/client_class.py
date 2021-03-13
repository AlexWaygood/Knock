from queue import Queue
from time import time

from src.network.network_abstract_class import Network, GetTime

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay, get_ticks as GetTicks


class Client(Network):
	__slots__ = 'addr', 'ConnectionMessage', 'SendQueue', 'ReceiveQueue', 'LastUpdate'

	def __init__(
			self,
			IP: str,
			port: int,
			password: str
	):
		super().__init__()
		self.addr = (IP, port)
		self.SendQueue = Queue()
		self.ReceiveQueue = Queue(maxsize=1)
		self.LastUpdate = 0

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
					from src.network.password_checker_client import ClientPasswordChecker as PasswordChecker
					PasswordChecker(self, self.conn, password)  # Sends the password to the server in __init__()

				print(f'Connected at {GetTime()}.')
				self.ClientReceive(connecting=True)
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

	# Called ClientReceive to distinguish from method in parent class
	def ClientReceive(self, connecting: bool = False):
		Info = self.receive(self.conn, connecting=connecting)
		self.LastUpdate = GetTicks()
		self.ReceiveQueue.put(Info)

	def BlockingMessageToServer(self, message: str = '@G'):
		if message:
			self.SendQueue.put(message)

		while not self.SendQueue.empty():
			delay(100)

	# Called ClientSend to distinguish from method in parent class
	def ClientSend(self, message: str):
		if len(message) > 10:
			self.conn.sendall(f'{len(message):-<10}'.encode())
			self.conn.sendall(message.encode())
		else:
			self.conn.sendall(f'{message}:-<10'.encode())

		self.ClientReceive()

	def CloseDown(self):
		self.ClientSend('@T')
		self.CloseConnection(self.conn)
