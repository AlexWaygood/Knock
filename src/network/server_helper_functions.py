from __future__ import annotations

from typing import TYPE_CHECKING
from socket import SHUT_RDWR
from traceback_with_variables import printing_exc

from src.players.players_server import ServerPlayer as Player
from src.network.network_abstract import GetTime
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.network.network_server import Server
	from socket import socket
	from src.game.server_game import ServerGame as Game


def CommsWithClient(
		S: Server,
		conn: socket,
		game: Game) -> None:

	data = S.receive(conn)
	Result = game.Operations[data[:2]](data)
	player = S.ConnectionInfo[conn]

	if not data or Result == 'Terminate':
		print(f'Connection with {player.addr} was broken at {GetTime()}.\n')

		try:
			del player
			conn.shutdown(SHUT_RDWR)
			conn.close()
		finally:
			raise Exception('Connection was terminated.')

	elif Result == 'pong' or player.NothingToSend():
		player.ScheduleSend('pong')


def EternalGameLoop(
		game: Game,
		server: Server
):
	with printing_exc():
		while not Player.AllPlayersHaveJoinedTheGame():
			delay(100)

		try:
			while True:
				game.PlayGame()
		finally:
			try:
				server.CloseDown()
			except:
				quit()
