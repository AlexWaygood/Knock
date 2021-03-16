#! Python3

"""This script must be run by exactly one machine for a game to take place."""
from __future__ import annotations

from src.initialisation.maximise_window import MaximiseWindow
MaximiseWindow()

from threading import Thread
from typing import TYPE_CHECKING
from logging import debug
from socket import SHUT_RDWR

from src.network.network_abstract_class import GetTime
from src.network.server_class import Server, AccessToken

from src.initialisation.ascii_suits import PrintIntroMessage
from src.initialisation.server_user_inputs import UserInputs
from src.initialisation.logging_config import LoggingConfig

from src.game.server_game import ServerGame as Game
from src.players.players_server import ServerPlayer as Player

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import ConnectionAddress
	from socket import socket


LoggingConfig(False)
debug('\n\nNEW RUN OF PROGRAMME STARTING\n\n')
PrintIntroMessage()
NumberOfPlayers, BiddingSystem, password, ManuallyVerify = UserInputs()
game = Game(NumberOfPlayers)


def CommsWithClient(S: Server,
                    player: Player,
                    conn: socket,
                    addr: ConnectionAddress,
                    game: Game = game) -> None:

	data = S.receive(conn)
	Result = game.Operations[data[:2]](data)

	if not data or Result == 'Terminate':
		print(f'Connection with {addr} was broken at {GetTime()}.\n')

		try:
			game.gameplayers.remove(player)
			conn.shutdown(SHUT_RDWR)
			conn.close()
		finally:
			raise Exception('Connection was terminated.')

	elif Result == 'pong':
		ToExport = Result
	else:
		with game:
			ToExport = game.Export(player.playerindex)

	S.ConnectionInfo[conn]['SendQueue'].put(ToExport)


def ClientConnect(S: Server,
                  playerindex: int,
                  conn: socket,
                  addr: ConnectionAddress,
                  BiddingSystem: str = BiddingSystem,
                  game: Game = game) -> None:

	# We want the whole server script to fail if a single thread goes down,
	# since there's no point continuing a game if one of the players has left
	S.ConnectionInfo[conn]['SendQueue'].put(f'{game.PlayerNumber}{playerindex}{BiddingSystem}')
	print(f'Game sent to client {addr} at {GetTime()}.\n')
	S.ConnectionInfo[conn]['player'] = Player.AllPlayers[playerindex]


def EternalGameLoop(game: Game = game,
                    NumberOfPlayers: int = NumberOfPlayers):

	global Server_object

	while len(game.gameplayers) < NumberOfPlayers or any(not player.name for player in game.gameplayers):
		delay(100)

	try:
		while True:
			game.PlayGame()
	finally:
		try:
			Server_object.CloseDown()
		except:
			pass


print('Initialising server...')

# The server will accept new connections until the expected number of players have connected to the server.
# Remember - this part of the code will fail if the server's network router does not have port forwarding set up.
# (Warning does not apply if you are playing within one local area network.)
# Remember to take the port out when publishing this code online.

(thread := Thread(target=EternalGameLoop, name='Server gameplay thread', daemon=True)).start()

Server_object = Server(
	IP='127.0.0.1',
	port=5555,
	ManuallyVerify=(ManuallyVerify == 'yes'),
	ClientConnectFunction=ClientConnect,
	NumberOfPlayers=NumberOfPlayers,
	AccessToken=AccessToken,
	password=password,
	CommsFunction=CommsWithClient
)
