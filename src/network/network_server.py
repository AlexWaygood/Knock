from __future__ import annotations

from select import select
from logging import getLogger
from typing import TYPE_CHECKING, NoReturn, Literal, Union
from pyinputplus import inputYesNo

from src.network.network_abstract import Network, GetTime
from src.players.players_server import ServerPlayer as Player

# noinspection PyBroadException
try:
	from src.secret_passwords import ACCESS_TOKEN
except:
	ACCESS_TOKEN = ''

if TYPE_CHECKING:
	from src.special_knock_types import NetworkFunction, ConnectionDict, ConnectionAddress
	from socket import socket
	from src.game.server_game import ServerGame as Game
	from ipinfo.details import Details


log = getLogger(__name__)


def IP_info(
		details: Details,
		addr: ConnectionAddress
) -> None:

	messages = (
		f'Attempted connection from {details.city}, {details.region}, {details.country_name} at {GetTime()}.',
		f'IP, port: {addr}',
		f'Hostname: {details.hostname}'
	)

	for m in messages:
		print(m)
		log.debug(m)


class Server(Network):
	__slots__ = 'ConnectionInfo', 'ip_handler', 'password_checker_class', 'password'

	def __init__(self, password: str) -> None:
		super().__init__()
		self.ConnectionInfo: ConnectionDict = {}
		self.ip_handler = None
		self.password = password
		self.password_checker_class = None

		if password:
			try:
				from src.password_checker.password_server import ServerPasswordChecker as PasswordChecker
				self.password_checker_class = PasswordChecker
				PasswordChecker.password = password
			except ModuleNotFoundError:
				print('Password import failed; will be unable to check passwords for attempted connections.')

		if ACCESS_TOKEN:
			try:
				from ipinfo import getHandler
				self.ip_handler = getHandler(ACCESS_TOKEN)
			except ImportError:
				print("Encountered an error importing ipinfo; won't be able to provide info on IP addresses.")
				log.debug("Encountered an error importing ipinfo; won't be able to provide info on IP addresses.")
		else:
			print('Not checking IP addresses as no access token was supplied.')
			log.debug('Not checking IP addresses as no access token was supplied.')

	def Run(
			self,
			IP: str,
			port: int,
			ManuallyVerify: bool,
			CommsFunction: NetworkFunction,
			game: Game
	) -> NoReturn:

		log.debug('Initialising server...')
		print('Initialising server...')
		self.conn.bind((IP, port))
		self.conn.listen()
		NumberOfClients = 0
		log.debug(f'Ready to accept connections to the server (time {GetTime()}).\n')
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
						ManuallyVerify,
						game
					)

					Inputs.append(NewConn)
					Outputs.append(NewConn)
					NumberOfClients += 1

					if NumberOfClients == game.PlayerNumber:
						log.debug('Maximum number of connections received; no longer open for connections.')
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
	        ManuallyVerify: bool,
	        game: Game
	) -> Union[Literal[0], socket]:

		conn, addr = self.conn.accept()

		if self.ip_handler:
			# noinspection PyBroadException
			try:
				IP_info(self.ip_handler.getDetails(addr[0]), addr)
			except:
				m = f"Couldn't get requested info for this IP address {addr}."
				print(m)
				log.debug(m)

		if self.ip_handler and ManuallyVerify:
			if inputYesNo('\nAccept this connection? ') == 'no':
				self.CloseConnection(conn)
				return 0

		if self.password:
			Checker = self.password_checker_class(self, conn)

			if not Checker.CheckPassword():
				m = f'Client {addr} entered the wrong password; declining attempted connection.'
				print(m)
				log.debug(m)
				self.CloseConnection(conn)
				return 0

		player: Player = Player.player(NumberOfClients)
		self.ConnectionInfo[conn] = player.connect(addr, f'{game.PlayerNumber}{NumberOfClients}{game.BiddingSystem}')

		m = f'Connection info to client {addr} was placed on the send-queue at {GetTime()}.\n'
		print(m)
		log.debug(m)

		return conn

	def receive(self, conn: socket) -> str:
		Message = self.SubReceive(self.DefaultTinyMessageSize, conn).decode()
		Message = Message.split('-')[0]

		if Message[0].isdigit() and Message[1].isdigit():
			Message = self.SubReceive(int(Message), conn)

		log.debug(f'Message received from client: {Message}.')
		return Message

	def CloseDown(self) -> None:
		log.debug('Attempting to close the server down.')
		[self.CloseConnection(conn) for conn in self.ConnectionInfo]
