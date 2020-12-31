#! Python3

"""This script must be run by exactly one machine for a game to take place."""


import traceback

from Network import *
from PasswordChecker import *
from Game import Game
from Player import Player

from pyinputplus import inputInt, inputMenu, inputCustom
from collections import defaultdict

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


def CommsWithClient(Server, player, conn, addr, Operations=Operations):
	global game

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

	while not game.Sendable:
		pass

	Server.send(game, conn=conn)
	return True


def ThreadedClient(Server, playerindex, conn, addr):
	global game

	# We want the whole server script to fail if a single thread goes down,
	# since there's no point continuing a game if one of the players has left

	Server.send({'game': game, 'player': (player := Player(playerindex))}, conn=conn)
	print(f'Game sent to client {addr} at {GetTime()}.\n')

	while True:
		try:
			if not CommsWithClient(Server, player, conn, addr):
				break
		except:
			print(traceback.format_exc())
			print(f'Exception occurred at {GetTime()}')
			break


PasswordChoices = [
	"I want a new, randomly generated password for this game",
	"I've already got a password for this game",
	"I don't want a password for this game"
]

while True:
	NumberOfPlayers = inputInt('How many players will be playing? ', min=2, max=6)
	game = Game(NumberOfPlayers)
	print()

	if Choice := inputMenu(choices=PasswordChoices, prompt='Select whether you want to set a password for this game:\n\n',
	                       numbered=True, blank=True) == PasswordChoices[0]:

		password = GeneratePassword()
		print(f'\nYour randomly generated password for this session is {password}')
	elif Choice == PasswordChoices[1]:
		password = inputCustom(PasswordInput, '\nPlease enter the password for this session: ')
	else:
		password = ''

	ManuallyVerify = inputYesNo('\nDo you want to manually authorise each connection? '
	                            '(If "no", new connections will be accepted automatically '
	                            'if they have entered the correct password.) ', blank=True) == 'yes'

	print('Initialising server...')

	# The server will accept new connections until the expected number of players have connected to the server.
	# Remember - this part of the code will fail if the server's network router does not have port forwarding set up.
	# (Warning does not apply if you are playing within one local area network.)
	# Remember to take the port out when publishing this code online.

	Server = Network('', 5555, ManuallyVerify, ThreadedClient, True, NumberOfPlayers,
	                 AccessToken=AccessToken, password=password)

	while len(game.gameplayers) < NumberOfPlayers or any(not player.name for player in game.gameplayers):
		pg.time.delay(60)

	try:
		GamesPlayed = 0
		while True:
			game.PlayGame()
			GamesPlayed += 1
	finally:
		try:
			Server.CloseDown()
		except:
			pass

	if inputYesNo('The server has closed down. Would you like to reinitialise and play again? ') == 'no':
		pg.quit()
		quit()
