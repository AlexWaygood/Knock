from __future__ import annotations

from select import select
from logging import getLogger
from typing import TYPE_CHECKING
from pyinputplus import inputYesNo

from src.network.network_abstract_class import Network, GetTime
from src.players.players_server import ServerPlayer as Player

if TYPE_CHECKING:
	from src.special_knock_types import NetworkFunction, ConnectionDict
	from ipinfo.handler import Handler
	from socket import socket


log = getLogger(__name__)
AccessToken = '62e82f844db51d'


class Server(Network):
	__slots__ = 'ConnectionInfo'

	def __init__(
			self,
			IP: str,
			port: int,
			ManuallyVerify: bool,
			BiddingSystem: str,
			NumberOfPlayers: int,
			AccessToken: str,
			password: str,
			CommsFunction: NetworkFunction
	):

		super().__init__(log)
		self.ConnectionInfo: ConnectionDict = {}
		self.conn.bind((IP, port))
		self.conn.listen()

		NumberOfClients = 0
		Handler_object = None

		if AccessToken:
			try:
				from ipinfo import getHandler
				Handler_object = getHandler(AccessToken)
			except:
				print("Encountered an error import ipinfo; won't be able to provide info on IP addresses.")
		else:
			print('Not checking IP addresses as no access token was supplied.')

		print(f'Ready to accept connections to the server (time {GetTime()}).\n')

		Inputs, Outputs = [self.conn], []

		while True:
			readable, writable, exceptional = select(Inputs, Outputs, Inputs)
			for s in readable:
				if s is self.conn and NumberOfClients < NumberOfPlayers:

					# if the server itself is appearing in the 'readable' list,
					# that means the server is ready to accept a new connection

					# Append the new connection to the 'inputs' list after the connection is established,
					# so we'll know to look for incoming data from that connection.

					# Append it also to the 'outputs' list after the connection is established,
					# so the server will know to check if that connection is ready to have data sent to it.

					NewConn = self.Connect(
						Handler_object,
						NumberOfClients,
						password,
						ManuallyVerify,
						NumberOfPlayers,
						BiddingSystem
					)

					Inputs.append(NewConn)
					Outputs.append(NewConn)
					NumberOfClients += 1

					if NumberOfClients == NumberOfPlayers:
						print('Maximum number of connections received; no longer open for connections.')
				else:
					CommsFunction(self, s)

			for s in writable:
				if not (Q := self.ConnectionInfo[s].SendQ).empty():
					Message = Q.get()
					self.send(Message, conn=s)

			if exceptional:
				raise Exception('Exception in one of the client threads!')

	def Connect(self,
	            Handler_object: Handler,
	            NumberOfClients: int,
	            password: str,
	            ManuallyVerify: bool,
	            NumberOfPlayers: int,
	            BiddingSystem: str):

		conn, addr = self.conn.accept()

		if Handler_object:
			try:
				# Should change this to addr[0] when other computers need to connect
				details = Handler_object.getDetails('86.14.41.223')

				print(
					f'Attempted connection from {details.city}, '
					f'{details.region}, {details.country_name} at {GetTime()}.'
				)

				print(f'IP, port: {addr}')
				print(f'Hostname: {details.hostname}')
			except:
				print(f"Couldn't get requested info for this IP address {addr}.")

		if Handler_object and ManuallyVerify:
			if inputYesNo('\nAccept this connection? ') == 'no':
				self.CloseConnection(conn)
				return 0

		if password:
			from src.network.password_checker_server import ServerPasswordChecker as PasswordChecker
			Checker = PasswordChecker(self, conn)

			if not Checker.CheckPassword(conn, password):
				print('Client entered the wrong password; declining attempted connection.')
				self.CloseConnection(conn)
				return 0

		player = Player.AllPlayers[NumberOfClients]
		player.addr = addr
		self.ConnectionInfo[conn] = player
		self.ConnectionInfo[conn].SendQ.put(f'{NumberOfPlayers}{NumberOfClients}{BiddingSystem}')
		print(f'Connection info to client {addr} was placed on the send-queue at {GetTime()}.\n')
		return conn

	@staticmethod
	def send(message: str,
	         conn: socket):

		# Create a header telling the other computer the size of the data we want to send.
		# Turn the header into a fixed-length message using f-string left-alignment, encode it, send it.
		# Then send the main message itself.
		if len(message) > 10:
			conn.sendall(f'{len(message):-<10}'.encode())
			conn.sendall(message.encode())
		else:
			conn.sendall(f'{message:-<10}'.encode())

		log.debug(f'Message sent to client: {message}.')

	def receive(self, conn: socket):
		Message = self.SubReceive(10, conn)
		Message = Message.split('-')[0]

		if Message[0].isdigit() and Message[1].isdigit():
			Message = self.SubReceive(int(Message), conn)

		log.debug(f'Message received from client: {Message}.')
		return Message

	def CloseDown(self):
		log.debug('Attempting to close the server down.')
		self.ConnectionInfo = [self.CloseConnection(conn) for conn in self.ConnectionInfo]
