#! Python3

"""This script must be run by exactly one machine for a game to take place."""

import socket

from src.Network.AbstractNetwork import GetTime
from src.Network.ServerClass import Server, AccessToken
from src.Network.AbstractPasswordChecker import GeneratePassword, PasswordInput
from src.Game.ServerGame import ServerGame as Game
from src.Players.ServerPlayers import ServerPlayer as Player

from pyinputplus import inputInt, inputMenu, inputCustom, inputYesNo
from threading import Thread

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay


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


def CommsWithClient(Server, player, conn, addr, game=game):
	"""
	@type Server: Server
	@type player: ServerPlayer
	@type conn: socket.socket
	@type addr: tuple
	@type game: ServerGame
	"""

	data = Server.receive(conn)

	if not data or game.Operations[data[:2]](data) == 'Terminate':
		print(f'Connection with {addr} was broken at {GetTime()}.\n')

		try:
			game.gameplayers.remove(player)
			conn.shutdown(socket.SHUT_RDWR)
			conn.close()
		finally:
			raise Exception('Connection was terminated.')

	with game:
		Server.ConnectionInfo[conn]['SendQueue'].put(game.Export(player.playerindex))


def ClientConnect(Server, playerindex, conn, addr, BiddingSystem=BiddingSystem, game=game):
	"""
	@type Server: Server
	@type playerindex: int
	@type conn: socket.socket
	@type addr: tuple
	@type BiddingSystem: str
	@type game: ServerGame
	"""

	# We want the whole server script to fail if a single thread goes down,
	# since there's no point continuing a game if one of the players has left
	Server.ConnectionInfo[conn]['SendQueue'].put(f'{game.PlayerNumber}{playerindex}{BiddingSystem}')
	print(f'Game sent to client {addr} at {GetTime()}.\n')
	Server.ConnectionInfo[conn]['player'] = Player.AllPlayers[playerindex]


def EternalGameLoop(game=game, NumberOfPlayers=NumberOfPlayers):
	"""
	@type game: ServerGame
	@type NumberOfPlayers: int
	"""

	global Server

	while len(game.gameplayers) < NumberOfPlayers or any(not player.name for player in game.gameplayers):
		delay(100)

	try:
		while True:
			game.PlayGame()
	finally:
		try:
			Server.CloseDown()
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

Server = Server(
	IP='127.0.0.1',
	port=5555,
	ManuallyVerify=(ManuallyVerify == 'yes'),
	ClientConnectFunction=ClientConnect,
	NumberOfPlayers=NumberOfPlayers,
	AccessToken=AccessToken,
	password=password,
	CommsFunction=CommsWithClient
)
