"""The server for the game."""

from __future__ import annotations

from select import select
from logging import getLogger
from typing import TYPE_CHECKING, NoReturn, Literal, Union
from pyinputplus import inputYesNo

from src import config as rc
from src.network import Network, get_time
from src.players.players_server import ServerPlayer as Player

try:
	from src.secret_passwords import ACCESS_TOKEN
except ModuleNotFoundError:
	ACCESS_TOKEN = ''

if TYPE_CHECKING:
	from src.special_knock_types import NetworkFunction, ConnectionDict, ConnectionAddress
	from socket import socket
	from src.game.server_game import ServerGame as Game
	from ipinfo.details import Details as IPAddressDetails


log = getLogger(__name__)


def report_ip_info(ip_details: IPAddressDetails, ip_address: ConnectionAddress) -> None:
	"""Print and log information regarding an IP address."""

	messages = (
		f'Attempted connection from {ip_details.city}, {ip_details.region}, {ip_details.country_name} at {get_time()}.',
		f'IP, port: {ip_address}',
		f'Hostname: {ip_details.hostname}'
	)

	for m in messages:
		print(m)
		log.debug(m)


class Server(Network):
	"""The network server."""

	__slots__ = {
		'connection_info': 'A dictionary mapping sockets to `Player` objects',
		'ip_handler': 'An object that will fetch info regarding the IP addresses of computers trying to connect',
		'password_checker_class': 'A class to handle the checking of passwords',
		'password': 'The password for users to connect to the game'
	}

	def __init__(self, password: str) -> None:
		super().__init__()
		self.connection_info: ConnectionDict = {}
		self.password = password

		password_checker_class, ip_handler = None, None

		if password:
			try:
				from src.password_checker.password_server import ServerPasswordChecker as PasswordChecker
				password_checker_class = PasswordChecker
				PasswordChecker.password = password
			except ModuleNotFoundError:
				print('Password import failed; will be unable to check passwords for attempted connections.')

		self.password_checker_class = password_checker_class

		if ACCESS_TOKEN:
			try:
				from ipinfo import getHandler
				ip_handler = getHandler(ACCESS_TOKEN)
			except ModuleNotFoundError:
				print("Encountered an error importing ipinfo; won't be able to provide info on IP addresses.")
				log.debug("Encountered an error importing ipinfo; won't be able to provide info on IP addresses.")
		else:
			print('Not checking IP addresses as no access token was supplied.')
			log.debug('Not checking IP addresses as no access token was supplied.')

		self.ip_handler = ip_handler

	def run(
			self,
			/,
			ip_addr: str,
			port: int,
			*,
			manually_verify: bool,
			comms_function: NetworkFunction,
			game: Game
	) -> NoReturn:
		"""Continually send and receive messages between the server and the clients as required, until the game ends."""

		log.debug('Initialising server...')
		print('Initialising server...')
		self.conn.bind((ip_addr, port))
		self.conn.listen()
		number_of_clients = 0
		log.debug(f'Ready to accept connections to the server (time {get_time()}).\n')
		print(f'Ready to accept connections to the server (time {get_time()}).\n')

		inputs, outputs = [self.conn], []

		while True:
			readable, writable, exceptional = select(inputs, outputs, inputs)
			for s in readable:
				if s is self.conn and number_of_clients < rc.player_number:

					# if the server itself is appearing in the 'readable' list,
					# that means the server is ready to accept a new connection

					# Append the new connection to the 'inputs' list after the connection is established,
					# so we'll know to look for incoming data from that connection.

					# Append it also to the 'outputs' list after the connection is established,
					# so the server will know to check if that connection is ready to have data sent to it.

					new_conn = self.connect(
						number_of_clients=number_of_clients,
						manually_verify=manually_verify
					)

					inputs.append(new_conn)
					outputs.append(new_conn)
					number_of_clients += 1

					if number_of_clients == rc.player_number:
						log.debug('Maximum number of connections received; no longer open for connections.')
						print('Maximum number of connections received; no longer open for connections.')
				else:
					comms_function(self, s, game)

			for s in writable:
				with self.connection_info[s].send_q as q:
					self.send(q.get(), s)
					log.debug(f'Message sent to client: {q.last_update}.')

			if exceptional:
				raise Exception('Exception in one of the client threads!')

	def connect(self, /, *, number_of_clients: int, manually_verify: bool) -> Union[Literal[0], socket]:
		"""Connect to a a client."""

		conn, addr = self.conn.accept()

		if self.ip_handler:
			# noinspection PyBroadException
			try:
				report_ip_info(self.ip_handler.getDetails(addr[0]), addr)
			except BaseException:
				m = f"Couldn't get requested info for this IP address {addr}."
				print(m)
				log.debug(m)

		if self.ip_handler and manually_verify:
			if inputYesNo('\nAccept this connection? ') == 'no':
				self.close_connection(conn)
				return 0

		if self.password:
			checker = self.password_checker_class(self, conn)

			if not checker.check_password():
				m = f'Client {addr} entered the wrong password; declining attempted connection.'
				print(m)
				log.debug(m)
				self.close_connection(conn)
				return 0

		player = Player(number_of_clients)
		self.connection_info[conn] = player.connect(addr, f'{rc.player_number}{number_of_clients}{rc.bidding_system}')

		m = f'Connection info to client {addr} was placed on the send-queue at {get_time()}.\n'
		print(m)
		log.debug(m)

		return conn

	def receive(self, conn: socket) -> str:
		"""Receive a message from a client."""

		message = self.sub_receive(self.default_tiny_message_size, conn).decode()
		message = message.split('-')[0]

		if message[0].isdigit() and message[1].isdigit():
			message = self.sub_receive(int(message), conn)

		log.debug(f'Message received from client: {message}.')
		return message

	def close_down(self) -> None:
		"""Shut down the server and all client connections."""

		log.debug('Attempting to close the server down.')
		[self.close_connection(conn) for conn in self.connection_info]
