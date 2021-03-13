#! Python3

"""This script must be run by exactly one machine for a game to take place."""
from __future__ import annotations

import socket

from pyinputplus import inputInt, inputMenu, inputCustom, inputYesNo
from threading import Thread
from typing import TYPE_CHECKING

from src.network.network_abstract_class import GetTime
from src.network.server_class import Server, AccessToken
from src.network.password_checker_abstract import GeneratePassword, PasswordInput
from src.game.server_game import ServerGame as Game
from src.players.players_server import ServerPlayer as Player

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import ConnectionAddress


print('Welcome to Knock!')
NumberOfPlayers = inputInt('How many players will be playing? ', min=2, max=6)
print()

game = Game(NumberOfPlayers)

BiddingRuleChoices = [
	'Classic rules (players decide what they will bid prior to each round)',
	'Anna Benjer rules (bids are randomly generated for each player prior to each round)'
]

BiddingSystem = inputMenu(
	choices=BiddingRuleChoices,
	prompt='Which variant of the rules will this tournament use?\n\n',
	numbered=True,
	blank=True
)

BiddingSystem = 'Random' if BiddingSystem == BiddingRuleChoices[1] else 'Classic'
print()


def CommsWithClient(S: Server,
                    player: Player,
                    conn: socket.socket,
                    addr: ConnectionAddress,
                    game: Game = game):

	data = S.receive(conn)
	Result = game.Operations[data[:2]](data)

	if not data or Result == 'Terminate':
		print(f'Connection with {addr} was broken at {GetTime()}.\n')

		try:
			game.gameplayers.remove(player)
			conn.shutdown(socket.SHUT_RDWR)
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
                  conn: socket.socket,
                  addr: ConnectionAddress,
                  BiddingSystem: str = BiddingSystem,
                  game: Game = game) -> None:

	# We want the whole server script to fail if a single thread goes down,
	# since there's no point continuing a game if one of the players has left
	S.ConnectionInfo[conn]['SendQueue'].put(f'{game.PlayerNumber}{playerindex}{BiddingSystem}')
	print(f'Game sent to client {addr} at {GetTime()}.\n')
	S.ConnectionInfo[conn]['player'] = Player.AllPlayers[playerindex]


def EternalGameLoop(game=game, NumberOfPlayers=NumberOfPlayers):
	"""
	@type game: ServerGame
	@type NumberOfPlayers: int
	"""

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


PasswordChoices = [
	"I want a new, randomly generated password for this game",
	"I've already got a password for this game",
	"I don't want a password for this game"
]

Choice = inputMenu(
	choices=PasswordChoices,
	prompt='Select whether you want to set a password for this game:\n\n',
	numbered=True,
	blank=True
)

if Choice == PasswordChoices[0]:
	password = GeneratePassword()
	print(f'\nYour randomly generated password for this session is {password}')
elif Choice == PasswordChoices[1]:
	password = inputCustom(PasswordInput, '\nPlease enter the password for this session: ')
else:
	password = ''

print()

ManuallyVerify = inputYesNo(
	'\nDo you want to manually authorise each connection? '
	'(If "no", new connections will be accepted automatically if they have entered the correct password.) ',
	blank=True
)

print('Initialising server...')

# The server will accept new connections until the expected number of players have connected to the server.
# Remember - this part of the code will fail if the server's network router does not have port forwarding set up.
# (Warning does not apply if you are playing within one local area network.)
# Remember to take the port out when publishing this code online.

(thread := Thread(target=EternalGameLoop, daemon=True)).start()

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
