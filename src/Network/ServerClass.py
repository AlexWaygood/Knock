import select

from typing import Callable
from queue import Queue
from pyinputplus import inputYesNo

from src.Network.AbstractNetwork import Network, GetTime


class Server(Network):
	__slots__ = 'ConnectionInfo'

	def __init__(self, IP, port, ManuallyVerify, ClientConnectFunction: Callable,
	             NumberOfPlayers, AccessToken, password, CommsFunction: Callable):

		"""
		@type IP: str
		@type port: int
		@type ManuallyVerify: bool
		@type ClientConnectFunction: Callable
		@type NumberOfPlayers: int
		@type AccessToken: str
		@type password: str
		@type CommsFunction: Callable
		"""

		super().__init__()
		self.ConnectionInfo = {}
		self.conn.bind((IP, port))
		self.conn.listen()

		NumberOfClients = 0

		try:
			handler = IPHandler(AccessToken) if AccessToken else None
		except:
			handler = None

		print(f'Ready to accept connections to the server (time {GetTime()}).\n')

		Inputs, Outputs = [self.conn], []

		while True:
			readable, writable, exceptional = select.select(Inputs, Outputs, Inputs)
			for s in readable:
				if s is self.conn and NumberOfClients < NumberOfPlayers:

					# if the server itself is appearing in the 'readable' list,
					# that means the server is ready to accept a new connection

					# Append the new connection to the 'inputs' list after the connection is established,
					# so we'll know to look for incoming data from that connection.

					# Append it also to the 'outputs' list after the connection is established,
					# so the server will know to check if that connection is ready to have data sent to it.

					NewConn = self.Connect(
						ClientConnectFunction,
						handler,
						NumberOfClients,
						password,
						ManuallyVerify
					)

					Inputs.append(NewConn)
					Outputs.append(NewConn)
					NumberOfClients += 1

					if NumberOfClients == NumberOfPlayers:
						print('Maximum number of connections received; no longer open for connections.')
				else:
					CommsFunction(self, self.ConnectionInfo[s]['player'], s, self.ConnectionInfo[s]['addr'])

			for s in writable:
				if not (Q := self.ConnectionInfo[s]['SendQueue']).empty():
					self.send(Q.get(), conn=s)

			if exceptional:
				raise Exception('Exception in one of the client threads!')

	def Connect(self, ClientConnectFunction, handler, NumberOfClients, password, ManuallyVerify):
		"""
		@type ClientConnectFunction: Callable
		@type handler: IPHandler
		@type NumberOfClients: int
		@type password: str
		@type ManuallyVerify: bool
		"""

		conn, addr = self.conn.accept()

		if handler:
			handler.CheckIPDetails(addr)

		if handler and ManuallyVerify:
			if inputYesNo('\nAccept this connection? ') == 'no':
				self.CloseConnection(conn)
				return 0

		if password:
			from src.Network.ServerPasswordChecker import ServerPasswordChecker as PasswordChecker
			Checker = PasswordChecker(self, conn)

			if not Checker.CheckPassword(conn, password):
				print('Client entered the wrong password; declining attempted connection.')
				self.CloseConnection(conn)
				return 0

		self.ConnectionInfo[conn] = {'SendQueue': Queue(), 'addr': addr}
		ClientConnectFunction(self, NumberOfClients, conn, addr)
		return conn

	# noinspection PyTypeChecker
	def CloseDown(self):
		self.ConnectionInfo = [self.CloseConnection(conn) for conn in self.ConnectionInfo]


AccessToken = '62e82f844db51d'


class IPHandler:
	"""Non-essential class to provide information on where attempted connections to the server are coming from."""
	__slots__ = 'handler'

	def __init__(self, AccessToken: str):
		try:
			import ipinfo
			self.handler = ipinfo.getHandler(AccessToken)
		except:
			print("Couldn't import ipinfo; will not be able to give information on attempted connections.")
			self.handler = None

	def CheckIPDetails(self, addr: tuple):
		if self.handler:
			try:
				# Should change this to addr[0] when other computers need to connect
				details = self.handler.getDetails('86.14.41.223')

				print(f'Attempted connection from {details.city}, '
				      f'{details.region}, {details.country_name} at {GetTime()}.')

				print(f'IP, port: {addr}')
				print(f'Hostname: {details.hostname}')
			except:
				print(f"Couldn't get requested info for this IP address {addr}.")
