"""Functions controlling the gameplay sequence for the client."""

from typing import NoReturn
from random import randint
from traceback_with_variables import printing_exc

import src.config as rc
from src.static_constants import StandardFonts, ContextConstants, BiddingChoices
from src.players.players_client import ClientPlayer as Players

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
from pygame.time import delay

game = rc.game
display_manager = rc.display_manager
typewriter = rc.typewriter
client = rc.client
player: Players = Players(rc.playerindex)
BiddingSystem = rc.bidding_system
context = rc.input_context


with ContextConstants as c:
	MESSAGE, FONT, GAME_UPDATES_NEEDED, CLICK_TO_START, TRICK_CLICK_NEEDED, TYPING_NEEDED, GAME_RESET, FIREWORKS = c


def play() -> NoReturn:
	"""Play a tournament of Knock."""

	with printing_exc():
		play_tournament()


def play_tournament() -> NoReturn:
	"""Gameplay sequence for an entire tournament of Knock."""

	# Menu sequence
	with context(TypingNeeded=True, Message='Please enter your name', font=StandardFonts.STANDARD_MASSIVE_FONT):
		while isinstance(player.name, int):
			delay(100)

	client.blocking_message_to_server(message='')
	delay(100)

	kwargs = {
		ContextConstants.MESSAGE: 'Waiting for all players to connect and enter their player_names',
		ContextConstants.FONT: StandardFonts.STANDARD_MASSIVE_FONT,
		ContextConstants.GAME_UPDATES_NEEDED: True
	}

	with context(**kwargs):
		while not Players.all_players_named:
			delay(100)

	while True:
		with game.context(game_in_progress=True):
			play_game(games_played=game.games_played)
		game.games_played += 1


def play_game(*, games_played: int) -> None:
	"""Gameplay sequence for an entire game of Knock."""

	game_initialisation(games_played=games_played)
	attribute_wait('StartNumberSet')

	for roundnumber, cardnumber, RoundLeader in zip(*game.get_game_parameters()):
		play_round(roundnumber, cardnumber, RoundLeader, games_played)

	end_game(games_played=games_played)


def game_initialisation(*, games_played: int) -> None:
	"""Gameplay sequence during the initialisation sequence
	The initialisation sequence involves entering players' names and how many cards the game will start with, etc.
	"""

	if games_played:
		type_msg('NEW GAME STARTING:', wait_afterwards=1000)

	if playerindex() and games_played:
		text = f"Waiting for {Players(0)} to decide how many cards the game will start with."

	elif playerindex():
		text = (
			f"As the first player to join this game, it is {Players(0)}'s "
			f"turn to decide how many cards the game will start with."
		)

	elif games_played:
		type_msg('Your turn to decide the starting card number!')
		text = "Please enter how many cards you wish the game to start with:"

	else:
		text = (
			"As the first player to join this game, it is your turn to decide "
			"how many cards you wish the game to start with:"
		)

	type_msg(text, wait_afterwards=0)

	with context(GameUpdatesNeeded=True, Message=text, font=StandardFonts.STANDARD_TITLE_FONT):
		context.typing_needed = not playerindex()
		while not game.start_card_no:
			delay(100)

	# Do some maths w.r.t. board dimensions, now that we know how many cards the game is going to start with.
	display_manager.get_hand_rects()

	type_msg('Click to start the game for all players!', wait_afterwards=0)

	kwargs = {
		CLICK_TO_START: True,
		GAME_UPDATES_NEEDED: True,
		MESSAGE: 'Click to start the game for all players!',
		FONT: StandardFonts.STANDARD_TITLE_FONT
	}

	with context(**kwargs):
		while not game.play_started:
			delay(100)

	display_manager.game_initialisation_fade()
	client.queue_message('@A')
	game.play_started = True


def play_round(round_number: int, card_number: int, round_leader: Players, games_played: int) -> None:
	"""Gameplay sequence during the playing of a round."""

	with game.context(round_in_progress=True):
		message = f'ROUND {round_number} starting! This round has {card_number} card{"s" if card_number != 1 else ""}.'
		message2 = f'{round_leader.name} starts this round.'

		for m in (message, message2):
			type_msg(m)

		if not games_played and round_number == 1:
			message = "Over the course of the game, your name will be underlined if it's your turn to play."
			message2 = 'Press the Tab key at any time to toggle in and out of full-screen mode.'

			type_msg(message)
			type_msg(message2)

		# wait for the server to make a new pack of cards.
		attribute_wait('new_pack')
		trump = game.trump_card
		type_msg(f'The trumpcard for this round is the {trump}, which has been removed from the pack.')

		# wait for the server to deal cards for this round.
		attribute_wait('CardsDealt')

		display_manager.round_start_fade()
		delay(250)

		if BiddingSystem == BiddingChoices.CLASSIC_BIDDING_SYSTEM:
			classic_bidding(round_number=round_number, games_played=games_played)
		else:
			random_bidding(round_number=round_number, card_number=card_number, games_played=games_played)

		client.blocking_message_to_server()

		# Announce what all the players are bidding this round.
		for message in Players.bid_text():
			type_msg(message)

		client.queue_message('@A')

		first_player_index = round_leader.player_index

		for i in range(card_number):
			first_player_index = play_trick(
				first_player_index=first_player_index,
				trick_number=(i + 1),
				card_number_this_round=card_number
			)

		display_manager.round_end_fade()

	client.queue_message('@A')

	delay(500)

	for message in Players.end_of_round_text(final_round=(card_number == 1)):
		type_msg(message)

	client.queue_message('@A')


def classic_bidding(*, round_number: int, games_played: int) -> None:
	"""Gameplay sequence during bidding at the beginning of a round.
	This function is only used if the 'classic bidding' option has been selected.
	"""

	if round_number == 1 and not games_played:
		type_msg('Cards for this round have been dealt; each player must decide what they will bid.')

	kwargs = {
		GAME_UPDATES_NEEDED: True,
		TYPING_NEEDED: True,
		MESSAGE: 'Please enter your bid:',
		FONT: StandardFonts.STANDARD_TITLE_FONT
	}

	with context(**kwargs):
		# We need to enter our bid.
		while player.bid == -1:
			delay(100)

		# We now need to wait until everybody else has bid.
		context.typing_needed = False
		i = playerindex()

		while not Players.all_bid():
			delay(100)
			context.text = Players.bid_waiting_text(i)


def random_bidding(*, round_number: int, card_number: int, games_played: int) -> None:
	"""Gameplay sequence during bidding at the beginning of a round.
	This function is only used if the 'random bidding' option has been selected.
	"""

	if round_number == 1 and not games_played:
		type_msg('Cards for this round have been dealt; each player must now bid.')

		type_msg(
			"The host for this game has decided that everybody's bid in this game "
			"will be randomly generated rather than decided"
		)

	bid = randint(0, card_number)
	type_msg(f'Your randomly generated bid for this round is {bid}!')

	with game as g:
		g.player_makes_bid(bid, playerindex())

	client.queue_message(f'@B{bid}')

	with context(GameUpdatesNeeded=True):
		while not Players.all_bid():
			delay(100)
			context.text = Players.bid_waiting_text(playerindex())


def play_trick(*, first_player_index: int, trick_number: int, card_number_this_round: int) -> int:
	"""Gameplay sequence during the playing of tricks_this_round."""

	player_order, pos_in_trick = game.start_trick(trick_number, first_player_index, player)

	with game.context(trick_in_progress=True):
		client.queue_message('@A')
		text = f'{f"TRICK {trick_number} starting" if card_number_this_round != 1 else "TRICK STARTING"}:'
		type_msg(text)

		# Make sure the server is ready for the trick to start.
		attribute_wait('TrickStart')

		# Tell the server we're ready to play the trick.
		client.blocking_message_to_server('@A')

		game.play_trick(context, pos_in_trick)

		attribute_wait('TrickWinnerLogged')

	winner = game.trick_winner

	# Tell the server we've logged the winner
	client.queue_message('@A')

	delay(500)
	type_msg(f'{winner} won {f"trick {trick_number}" if card_number_this_round != 1 else "the trick"}!')
	display_manager.trick_end_fade()

	if trick_number != card_number_this_round:
		client.queue_message('@A')

	return winner.player_index


def end_game(*, games_played: int) -> None:
	"""Gameplay sequence at the end of a game."""

	display_manager.deactivate_hand()

	# Announce the final scores + who won the game.
	for text in Players.end_of_game_text():
		type_msg(text)

	game.play_started = False
	delay(500)

	display_manager.fireworks_sequence()

	# Announce who's currently won the most games in this tournament so far.
	if games_played:
		for text in Players.tournament_leaders_text():
			type_msg(text)

	message = 'Press the spacebar to play again with the same players, or close the window to exit the game.'
	type_msg(message, wait_afterwards=0)

	attribute_wait('new_game_reset', game_reset=True)
	game.new_game_reset()
	client.queue_message('@A')
	display_manager.clear_hand_rects()


def playerindex() -> int:
	"""Return the player_index of the client.
	This function has to be dynamic, as a player's player_index is liable to change between games.
	"""
	return player.player_index


def type_msg(message: str, /, *, wait_afterwards: int = 1200) -> None:
	"""Type a message on the typewriter (convenience function)."""
	typewriter.type(message, wait_afterwards=wait_afterwards)


def attribute_wait(attribute: str, /, *, game_reset: bool = False) -> None:
	kwargs = {
		GAME_UPDATES_NEEDED: True,
		GAME_RESET: game_reset
	}

	if game_reset:
		m = 'Press the spacebar to play again with the same players, or close the window to exit the game.'

		kwargs.update({
			MESSAGE: m,
			FONT: StandardFonts.STANDARD_TITLE_FONT
		})

	with context(**kwargs):
		game.attribute_wait(attribute)
