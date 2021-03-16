from __future__ import annotations

from random import randint
from traceback_with_variables import printing_exc
from typing import TYPE_CHECKING

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay

if TYPE_CHECKING:
	from src.players.players_client import (ClientPlayer as Player,
	                                        ClientGameplayers as Gameplayers)

	from src.display.display_manager import DisplayManager
	from src.display.input_context import InputContext
	from src.display.typewriter import Typewriter
	from src.game.client_game import ClientGame as Game
	from src.network.client_class import Client


def AttributeWait(
		Attribute: str,
		context: InputContext,
		game: Game,
		GameReset: bool = False
):

	Args = {
		'GameUpdatesNeeded': True,
		'GameReset': GameReset
	}

	if GameReset:
		M = 'Press the spacebar to play again with the same players, or close the window to exit the game.'

		Args.update({
			'Message': M,
			'font': 'Title'
		})

	with context(**Args):
		game.AttributeWait(Attribute)


def Play(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		player: Player,
		client: Client,
		BiddingSystem: str,
		displayManager: DisplayManager
):

	with printing_exc():
		PlayTournament(game, context, typewriter, player, client, BiddingSystem, displayManager)


def PlayTournament(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		player: Player,
		client: Client,
		BiddingSystem: str,
		displayManager: DisplayManager
):

	# Menu sequence
	with context(TypingNeeded=True, Message='Please enter your name', font='Massive'):
		while isinstance(player.name, int):
			delay(100)

	client.BlockingMessageToServer(message='')
	delay(100)

	Args = {
		'Message': 'Waiting for all players to connect and enter their names',
		'font': 'Massive',
		'GameUpdatesNeeded': True
	}

	with context(**Args):
		while not game.gameplayers.AllPlayersHaveJoinedTheGame():
			delay(100)

	while True:
		PlayGame(game, context, typewriter, game.GamesPlayed, player, client, BiddingSystem, displayManager)
		game.GamesPlayed += 1


def PlayGame(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		GamesPlayed: int,
		player: Player,
		client: Client,
		BiddingSystem: str,
		dM: DisplayManager
):

	GameInitialisation(game, context, typewriter, player, GamesPlayed, client, dM)
	AttributeWait('StartNumberSet', context, game)

	for roundnumber, cardnumber, RoundLeader in zip(*game.GetGameParameters()):
		PlayRound(
			game,
			context,
			typewriter,
			player,
			roundnumber,
			cardnumber,
			RoundLeader,
			GamesPlayed,
			client,
			dM,
			BiddingSystem
		)

	EndGame(game, context, typewriter, client, GamesPlayed, dM)


def GameInitialisation(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		player: Player,
		GamesPlayed: int,
		client: Client,
		displayManager: DisplayManager
):

	if GamesPlayed:
		Message = 'NEW GAME STARTING:'
		typewriter.Type(Message, WaitAfterwards=1000)

	if player.playerindex and GamesPlayed:
		text = f"Waiting for {game.gameplayers[0]} to decide how many cards the game will start with."

	elif player.playerindex:
		text = f"As the first player to join this game, it is {game.gameplayers[0]}'s " \
		       f"turn to decide how many cards the game will start with."

	elif GamesPlayed:
		Message2 = 'Your turn to decide the starting card number!'
		typewriter.Type(Message2)
		text = "Please enter how many cards you wish the game to start with:"

	else:
		text = "As the first player to join this game, it is your turn to decide " \
		       "how many cards you wish the game to start with:"

	typewriter.Type(text, WaitAfterwards=0)

	with context(GameUpdatesNeeded=True, Message=text, font='Title'):
		context.TypingNeeded = not player.playerindex
		while not game.StartCardNumber:
			delay(100)

	# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
	displayManager.HandSurf.GetHandRects()

	typewriter.Type('Click to start the game for all players!', WaitAfterwards=0)

	Args = {
		'ClickToStart': True,
		'GameUpdatesNeeded': True,
		'Message': 'Click to start the game for all players!',
		'font': 'Title'
	}

	with context(**Args):
		while not game.StartPlay:
			delay(100)

	displayManager.GameInitialisationFade(GamesPlayed)
	client.SendQueue.put('@A')
	game.StartPlay = True


def PlayRound(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		player: Player,
		RoundNumber: int,
		cardno: int,
		RoundLeader: Player,
		GamesPlayed: int,
		client: Client,
		dM: DisplayManager,
		BiddingSystem: str
):

	game.StartRound(cardno, RoundLeader.playerindex, RoundNumber)

	Message = f'ROUND {RoundNumber} starting! This round has {cardno} card{"s" if cardno != 1 else ""}.'
	Message2 = f'{RoundLeader.name} starts this round.'

	for m in (Message, Message2):
		typewriter.Type(m)

	if not GamesPlayed and RoundNumber == 1:
		Message = "Over the course of the game, your name will be underlined if it's your turn to play."
		Message2 = 'Press the Tab key at any time to toggle in and out of full-screen mode.'

		typewriter.Type(Message)
		typewriter.Type(Message2)

	# Wait for the server to make a new pack of cards.
	AttributeWait('NewPack', context, game)
	Trump = game.TrumpCard
	typewriter.Type(f'The trumpcard for this round is the {Trump}, which has been removed from the pack.')

	# Wait for the server to deal cards for this round.
	AttributeWait('CardsDealt', context, game)

	dM.RoundStartFade()
	delay(250)

	if BiddingSystem == 'Classic':
		ClassicBidding(typewriter, game.gameplayers, player, context, RoundNumber, GamesPlayed)
	else:
		RandomBidding(game, player, context, typewriter, RoundNumber, cardno, GamesPlayed, client)

	client.BlockingMessageToServer()

	# Announce what all the players are bidding this round.
	for Message in game.gameplayers.BidText():
		typewriter.Type(Message)

	client.SendQueue.put('@A')

	FirstPlayerIndex = RoundLeader.playerindex

	for i in range(cardno):
		FirstPlayerIndex = PlayTrick(game, context, typewriter, player, FirstPlayerIndex, (i + 1), cardno, client, dM)

	dM.RoundEndFade()

	# Award points etc.
	game.EndRound()
	client.SendQueue.put('@A')

	delay(500)

	for message in game.gameplayers.EndRoundText(FinalRound=(cardno == 1)):
		typewriter.Type(message)

	client.SendQueue.put('@A')


def ClassicBidding(
		typewriter: Typewriter,
		gameplayers: Gameplayers,
		player: Player,
		context: InputContext,
		RoundNumber: int,
		GamesPlayed: int
):

	if RoundNumber == 1 and not GamesPlayed:
		typewriter.Type('Cards for this round have been dealt; each player must decide what they will bid.')

	# We need to enter our bid.

	Args = {
		'GameUpdatesNeeded': True,
		'TypingNeeded': True,
		'Message': 'Please enter your bid:',
		'font': 'Title'
	}

	with context(**Args):
		while player.Bid == -1:
			delay(100)

		# We now need to wait until everybody else has bid.
		context.TypingNeeded = False
		i = player.playerindex

		while not gameplayers.AllBid():
			delay(100)
			context.Text = gameplayers.BidWaitingText(i)


def RandomBidding(
		game: Game,
		player: Player,
		context: InputContext,
		typewriter: Typewriter,
		RoundNumber: int,
		cardnumber: int,
		GamesPlayed: int,
		client: Client
):

	if RoundNumber == 1 and not GamesPlayed:
		typewriter.Type('Cards for this round have been dealt; each player must now bid.')

		typewriter.Type(
			"The host for this game has decided that everybody's bid in this game "
			"will be randomly generated rather than decided"
		)

	Bid = randint(0, cardnumber)
	typewriter.Type(f'Your randomly generated bid for this round is {Bid}!')

	with game:
		game.PlayerMakesBid(Bid, player.playerindex)

	client.SendQueue.put(f'@B{Bid}')

	with context(GameUpdatesNeeded=True):
		while not game.gameplayers.AllBid():
			delay(100)
			context.Text = game.gameplayers.BidWaitingText(player.playerindex)


def PlayTrick(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		player: Player,
		FirstPlayerIndex: int,
		TrickNumber: int,
		CardNumberThisRound: int,
		client: Client,
		displayManager: DisplayManager
):

	PlayerOrder, PosInTrick = game.StartTrick(TrickNumber, FirstPlayerIndex, player)
	client.SendQueue.put('@A')
	Text = f'{f"TRICK {TrickNumber} starting" if CardNumberThisRound != 1 else "TRICK STARTING"}:'
	typewriter.Type(Text)

	# Make sure the server is ready for the trick to start.
	AttributeWait('TrickStart', context, game)

	# Tell the server we're ready to play the trick.
	client.BlockingMessageToServer('@A')

	game.PlayTrick(context, PosInTrick)

	AttributeWait('TrickWinnerLogged', context, game)
	Winner = game.EndTrick()

	# Tell the server we've logged the winner
	client.SendQueue.put('@A')

	delay(500)
	typewriter.Type(f'{Winner} won {f"trick {TrickNumber}" if CardNumberThisRound != 1 else "the trick"}!')
	displayManager.TrickEndFade()

	if TrickNumber != CardNumberThisRound:
		client.SendQueue.put('@A')

	return Winner.playerindex


def EndGame(
		game: Game,
		context: InputContext,
		typewriter: Typewriter,
		client: Client,
		GamesPlayed: int,
		displayManager: DisplayManager
):

	displayManager.HandSurf.Deactivate()

	# Announce the final scores + who won the game.
	for text in game.gameplayers.GameCleanUp():
		typewriter.Type(text)

	game.StartPlay = False
	delay(500)

	displayManager.FireworksSequence()

	# Announce who's currently won the most games in this tournament so far.
	if GamesPlayed:
		for text in game.gameplayers.TournamentLeaders():
			typewriter.Type(text)

	Message = 'Press the spacebar to play again with the same players, or close the window to exit the game.'
	typewriter.Type(Message, WaitAfterwards=0)

	AttributeWait('NewGameReset', context, game, GameReset=True)
	game.NewGameReset()
	client.SendQueue.put('@A')
	displayManager.HandSurf.ClearRectList()
