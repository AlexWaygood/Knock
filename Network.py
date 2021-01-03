"""

Two classes that have to do with communications between the server and clients...
...plus a one-line function for returning the current time in a fixed format.

"""

import socket, pickle, select

from PasswordChecker import PasswordChecker
from HelperFunctions import GetTime

from queue import Queue
from pyinputplus import inputYesNo


AccessToken = '62e82f844db51d'


class Network(object):
	"""Class object for encoding communication protocols between the server and client."""

	__slots__ = 'conn', 'ConnectionInfo', 'IP', 'port', 'addr', 'InfoDict', 'server', 'ManuallyVerify', 'cipher',\
	            'PasswordChecker'

	def __init__(self, IP, port, ManuallyVerify=False, ClientConnectFunction=None, server=False,
	             NumberOfPlayers=0, AccessToken='', password='', CommsFunction=None):

		self.server = server
		self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		if server:
			self.ConnectionInfo = {}
			self.conn.bind((IP, port))
			self.conn.listen()

			NumberOfClients = 0

			try:
				handler = IPHandler(AccessToken) if AccessToken else None
			except:
				handler = None

			print(f'Ready to accept connections to the server (time {GetTime()}).\n')

			Inputs = Exceptions = [self.conn]
			Outputs = []

			while True:
				readable, writable, exceptional = select.select(Inputs, Outputs, Exceptions)
				for s in readable:
					if s is self.conn and NumberOfClients < NumberOfPlayers:

						# if the server itself is appearing in the 'readable' list,
						# that means the server is ready to accept a new connection

						# Append the new connection to the 'inputs' list after the connection is established,
						# so we'll know to look for incoming data from that connection.

						# Append it also to the 'outputs' list after the connection is established,
						# so the server will know to check if that connection is ready to have data sent to it.

						NewConn = self.ServerConnect(
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

		else:
			self.addr = (IP, port)
			self.InfoDict = self.ClientConnect(password)

	def ServerConnect(self, ClientConnectFunction, handler, NumberOfClients, password, ManuallyVerify):
		conn, addr = self.conn.accept()

		if handler:
			handler.CheckIPDetails(addr)

		if handler and ManuallyVerify:
			if inputYesNo('\nAccept this connection? ') == 'no':
				self.CloseConnection(conn)
				return 0

		if password:
			Checker = PasswordChecker(self, conn, True)

			if not Checker.ServerChecksPassword(conn, password):
				print('Client entered the wrong password; declining attempted connection.')
				self.CloseConnection(conn)
				return 0

		self.ConnectionInfo[conn] = {
			'SendQueue': Queue(),
			'addr': addr
		}

		ClientConnectFunction(self, NumberOfClients, conn, addr)
		return conn

	def ClientConnect(self, password):
		self.conn.connect(self.addr)

		if password:
			Checker = PasswordChecker(self, self.conn, False)
			Checker.ClientSendsPassword(password)

		return self.receive()

	def ClientSimpleSend(self, data):
		data = f'@{data[0]}--------'
		self.conn.sendall(data.encode())
		return self.receive()

	def send(self, messagetype='', data='', conn=None):
		if not conn:
			conn = self.conn

		if self.server:
			message = messagetype
		else:
			message = {
				'MessageType'   : messagetype,
				'Message'       : data
			}

		# Convert the data we want to send into binary.
		# Create a header telling the other computer the size of the data we want to send.
		# Turn the header into a fixed-length message, encode it.
		PickledMessage = pickle.dumps(message)
		Header = str(len(PickledMessage))
		Header = f'{Header}{"".join(("-" for i in range(10 - len(Header))))}'.encode()

		# Send the header, then the data.
		conn.sendall(Header)
		conn.recv(1)
		conn.sendall(PickledMessage)

		if not self.server:
			return self.receive()

	def receive(self, conn=None):
		if not conn:
			conn = self.conn

		InitialMessage = self.SubReceive(10, conn).decode()
		InitialMessage = ''.join((character for character in InitialMessage if character != '-'))

		if InitialMessage.startswith('@') or not InitialMessage[:2].isdigit():
			return InitialMessage[:2]

		AmountToReceive = int(InitialMessage)
		conn.sendall('1'.encode())

		return pickle.loads(self.SubReceive(AmountToReceive, conn))

	def SubReceive(self, AmountToReceive, conn=None):
		if not conn:
			conn = self.conn

		response = []

		while AmountToReceive > 0:
			chunk = (conn.recv(min(8192, AmountToReceive)))
			AmountToReceive -= len(chunk)
			response.append(chunk)

		# Can't decode it here, because we don't know if it's a str or a dict.
		return b''.join(response)

	@staticmethod
	def CloseConnection(conn):
		conn.shutdown(socket.SHUT_RDWR)
		conn.close()

	def CloseDown(self):
		if self.server:
			self.ConnectionInfo = [self.CloseConnection(conn) for conn in self.ConnectionInfo]
		else:
			self.ClientSimpleSend('Terminate')
			self.CloseConnection(self.conn)


class IPHandler(object):
	"""Non-essential class to provide information on where attempted connections to the server are coming from."""

	__slots__ = 'handler'

	def __init__(self, AccessToken):
		try:
			import ipinfo
			self.handler = ipinfo.getHandler(AccessToken)
		except:
			print("Couldn't import ipinfo; will not be able to give information on attempted connections.")
			self.handler = None

	def CheckIPDetails(self, addr):
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
