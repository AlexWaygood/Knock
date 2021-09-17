from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn
from socket import SHUT_RDWR
from traceback_with_variables import printing_exc

from src.players.players_server import ServerPlayer as Player
from src.network import get_time
# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import delay

if TYPE_CHECKING:
	from src.network.network_server import Server
	from socket import socket
	from src.game.server_game import ServerGame as Game


DEFAULT_SERVER_MESSAGE = 'pong'


def comms_with_client(
		s: Server,
		conn: socket,
		game: Game
) -> None:

	data = s.receive(conn)
	result = game.operations[data[:2]](data)
	player = s.connection_info[conn]

	if not data or result == 'Terminate':
		print(f'Connection with {player.addr} was broken at {get_time()}.\n')

		try:
			del player
			conn.shutdown(SHUT_RDWR)
			conn.close()
		finally:
			raise Exception('Connection was terminated.')

	elif result == DEFAULT_SERVER_MESSAGE or player.nothing_to_send:
		player.schedule_send(DEFAULT_SERVER_MESSAGE)


def eternal_game_loop(game: Game, server: Server) -> NoReturn:
	with printing_exc():
		while not Player.all_players_have_joined_the_game():
			delay(100)

		try:
			while True:
				game.play_game()
		finally:
			# noinspection PyBroadException
			try:
				server.close_down()
			except BaseException:
				quit()
