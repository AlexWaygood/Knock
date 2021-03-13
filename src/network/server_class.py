from __future__ import annotations

import select

from typing import TYPE_CHECKING
from queue import Queue
from pyinputplus import inputYesNo

from src.network.network_abstract_class import Network, GetTime

if TYPE_CHECKING:
	from src.special_knock_types import NetworkFunction
	from ipinfo.handler import Handler


AccessToken = '62e82f844db51d'


class Server(Network):
	__slots__ = 'ConnectionInfo'

	def __init__(self,
	             IP: str,
	             port: int,
	             ManuallyVerify: bool,
	             ClientConnectFunction: NetworkFunction,
	             NumberOfPlayers: int,
	             AccessToken: str,
	             password: str,
	             CommsFunction: NetworkFunction):

		super().__init__()
		self.ConnectionInfo = {}
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
						Handler_object,
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
					Message = Q.get()
					self.send(Message, conn=s)

			if exceptional:
				raise Exception('Exception in one of the client threads!')

	def Connect(self,
	            ClientConnectFunction: NetworkFunction,
	            Handler_object: Handler,
	            NumberOfClients: int,
	            password: str,
	            ManuallyVerify: bool):

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

		self.ConnectionInfo[conn] = {'SendQueue': Queue(), 'addr': addr}
		ClientConnectFunction(self, NumberOfClients, conn, addr)
		return conn

	# noinspection PyTypeChecker
	def CloseDown(self):
		self.ConnectionInfo = [self.CloseConnection(conn) for conn in self.ConnectionInfo]
