#! Python3

"""This script must be run by exactly one machine for a game to take place."""


import socket

from Network import Network, AccessToken
from Game import Game
from Player import Player
from HelperFunctions import GetTime
from PasswordChecker import GeneratePassword, PasswordInput

from pyinputplus import inputInt, inputMenu, inputCustom, inputYesNo
from collections import defaultdict
from threading import Thread

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg


print('Welcome to Knock!')

# This dictionary in some ways belongs as part of the Game class, but cannot be pickled.
# The Game class must be pickleable.

# Default operation is if the client is telling us which card they want to play
Operations = defaultdict(
	lambda: lambda game, Info: game.ExecutePlay(cardID=Info['Message'], playerindex=Info['playerindex'])
)

Operations.update({
	# if the client is just asking for an updated copy of the game
	'@G': lambda game, Info: None,

	# if the client is sending the name of that player
	'player': lambda game, Info: game.AddPlayerName(Info['Message'], Info['playerindex']),

	# if the client is telling us how many cards the game should start with
	'CardNumber': lambda game, Info: game.SetCardNumber(Info['Message']),

	# if the client is telling us the players are ready to start the game
	'@S': lambda game, Info: game.TimeToStart(),

	# if the client is telling us how many tricks they are going to bid in this round.
	'Bid': lambda game, Info: game.PlayerMakesBid(Info['Message'], playerindex=Info['playerindex']),

	# If the client is telling us whether they want an instant rematch after the game has ended.
	'@1': lambda game, Info: game.RepeatQuestionAnswer(),

	# If the client is saying they don't want a repeat game.
	'@T': lambda game, Info: 'Terminate',

	# If the client is telling us they've completed an animation sequence.
	'@A': lambda game, Info: game.PlayerActionCompleted(Info['playerindex'])
})


NumberOfPlayers = inputInt('How many players will be playing? ', min=2, max=6)
print()

game = Game(NumberOfPlayers)

BiddingRuleChoices = [
	'Classic rules (players decide what they will bid prior to each round)',
	'Anna Benjer rules (bids are randomly generated for each player prior to each round)'
]

BiddingSystem = inputMenu(
	choices=BiddingRuleChoices,
	prompt='Which variant of the rules will this tournament use?',
	numbered=True,
	blank=True
)

BiddingSystem = 'Random' if BiddingSystem == BiddingRuleChoices[1] else 'Classic'
print()


def CommsWithClient(Server, player, conn, addr, Operations=Operations, game=game):
	Broken = False
	playerindex = game.gameplayers.index(player)
	data = Server.receive(conn)

	if not data:
		Broken = True
	else:
		if isinstance(data, str):
			MessageType = Message = data
		else:
			MessageType, Message = data['MessageType'], data['Message']

		Info = {
			'Message': Message,
			'playerindex': playerindex
		}

		if Operations[MessageType](game, Info) == 'Terminate':
			Broken = True

	if Broken:
		print(f'Connection with {addr} was broken at {GetTime()}.\n')

		try:
			game.gameplayers.remove(player)
			conn.shutdown(socket.SHUT_RDWR)
			conn.close()
		finally:
			raise Exception('Connection was terminated.')

	while not game.SendableContext:
		pass

	Server.ConnectionInfo[conn]['SendQueue'].put(game)


def ClientConnect(Server, playerindex, conn, addr, BiddingSystem=BiddingSystem, game=game):
	# We want the whole server script to fail if a single thread goes down,
	# since there's no point continuing a game if one of the players has left
	player = Player(playerindex)
	Server.ConnectionInfo[conn]['SendQueue'].put({'game': game, 'player': player, 'BiddingSystem': BiddingSystem})
	print(f'Game sent to client {addr} at {GetTime()}.\n')
	Server.ConnectionInfo[conn]['player'] = player


def EternalGameLoop(game=game, NumberOfPlayers=NumberOfPlayers):
	global Server

	while len(game.gameplayers) < NumberOfPlayers or any(not player.name for player in game.gameplayers):
		pg.time.delay(100)

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

Server = Network(
	IP='127.0.0.1',
	port=5555,
	ManuallyVerify=(ManuallyVerify == 'yes'),
	ClientConnectFunction=ClientConnect,
	server=True,
	NumberOfPlayers=NumberOfPlayers,
	AccessToken=AccessToken,
	password=password,
	CommsFunction=CommsWithClient
)

thread.join()
