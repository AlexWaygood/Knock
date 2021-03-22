from __future__ import annotations

from select import select
from logging import getLogger
from typing import TYPE_CHECKING
from pyinputplus import inputYesNo

from src.network.network_abstract import Network, GetTime
from src.players.players_server import ServerPlayer as Player

if TYPE_CHECKING:
	from src.special_knock_types import NetworkFunction, ConnectionDict
	from socket import socket
	from src.game.server_game import ServerGame as Game


log = getLogger(__name__)
AccessToken = '62e82f844db51d'


class Server(Network):
	__slots__ = 'ConnectionInfo', 'ip_handler'

	def __init__(self, AccessToken: str):
		super().__init__()
		self.ConnectionInfo: ConnectionDict = {}
		self.ip_handler = None

		if AccessToken:
			try:
				from ipinfo import getHandler
				self.ip_handler = getHandler(AccessToken)
			except:
				print("Encountered an error importing ipinfo; won't be able to provide info on IP addresses.")
		else:
			print('Not checking IP addresses as no access token was supplied.')

	def Run(
			self,
			IP: str,
			port: int,
			ManuallyVerify: bool,
			password: str,
			CommsFunction: NetworkFunction,
			game: Game
	):
		print('Initialising server...')
		self.conn.bind((IP, port))
		self.conn.listen()
		NumberOfClients = 0
		print(f'Ready to accept connections to the server (time {GetTime()}).\n')

		Inputs, Outputs = [self.conn], []

		while True:
			readable, writable, exceptional = select(Inputs, Outputs, Inputs)
			for s in readable:
				if s is self.conn and NumberOfClients < game.PlayerNumber:

					# if the server itself is appearing in the 'readable' list,
					# that means the server is ready to accept a new connection

					# Append the new connection to the 'inputs' list after the connection is established,
					# so we'll know to look for incoming data from that connection.

					# Append it also to the 'outputs' list after the connection is established,
					# so the server will know to check if that connection is ready to have data sent to it.

					NewConn = self.Connect(
						NumberOfClients,
						password,
						ManuallyVerify,
						game
					)

					Inputs.append(NewConn)
					Outputs.append(NewConn)
					NumberOfClients += 1

					if NumberOfClients == game.PlayerNumber:
						print('Maximum number of connections received; no longer open for connections.')
				else:
					CommsFunction(self, s, game)

			for s in writable:
				with self.ConnectionInfo[s].SendQ as q:
					self.send(q.get(), s)
					log.debug(f'Message sent to client: {q.LastUpdate}.')

			if exceptional:
				raise Exception('Exception in one of the client threads!')

	def Connect(
			self,
	        NumberOfClients: int,
	        password: str,
	        ManuallyVerify: bool,
	        game: Game
	):

		conn, addr = self.conn.accept()

		if self.ip_handler:
			try:
				# Should change this to addr[0] when other computers need to connect
				details = self.ip_handler.getDetails('86.14.41.223')

				print(
					f'Attempted connection from {details.city}, '
					f'{details.region}, {details.country_name} at {GetTime()}.'
				)

				print(f'IP, port: {addr}')
				print(f'Hostname: {details.hostname}')
			except:
				print(f"Couldn't get requested info for this IP address {addr}.")

		if self.ip_handler and ManuallyVerify:
			if inputYesNo('\nAccept this connection? ') == 'no':
				self.CloseConnection(conn)
				return 0

		if password:
			from src.password_checker.password_server import ServerPasswordChecker as PasswordChecker
			Checker = PasswordChecker(self, conn)

			if not Checker.CheckPassword(conn, password):
				print('Client entered the wrong password; declining attempted connection.')
				self.CloseConnection(conn)
				return 0

		player = Player.player(NumberOfClients)
		player.addr = addr
		self.ConnectionInfo[conn] = player
		self.ConnectionInfo[conn].SendQ.put(f'{game.PlayerNumber}{NumberOfClients}{game.BiddingSystem}')
		print(f'Connection info to client {addr} was placed on the send-queue at {GetTime()}.\n')
		return conn

	def receive(self, conn: socket):
		Message = self.SubReceive(self.DefaultTinyMessageSize, conn)
		Message = Message.split('-')[0]

		if Message[0].isdigit() and Message[1].isdigit():
			Message = self.SubReceive(int(Message), conn)

		log.debug(f'Message received from client: {Message}.')
		return Message

	def CloseDown(self):
		log.debug('Attempting to close the server down.')
		self.ConnectionInfo = [self.CloseConnection(conn) for conn in self.ConnectionInfo]
