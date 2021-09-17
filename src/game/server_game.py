from __future__ import annotations

from traceback_with_variables import printing_exc
from typing import TYPE_CHECKING, NoReturn, Final

from src.game import AbstractGame, events_dict
from src.players.players_server import ServerPlayers as Players
from src.cards.server_card import ServerCard as Card, ServerPack as Pack

# noinspection PyUnresolvedReferences
from src import pre_pygame_import, config as rc
from pygame.time import delay

if TYPE_CHECKING:
	from src.special_knock_types import NumberInput, OptionalStr


DEFAULT_NETWORK_MESSAGE: Final = 'pong'
KILL_PROGRAMME_MESSAGE: Final = 'Terminate'


# noinspection PyPropertyDefinition
class ServerGame(AbstractGame[Card, Players]):
	"""Serverside simulation of a game of Knock."""

	__slots__ = 'operations', 'triggers'

	def __init__(self, /) -> None:
		super().__init__()
		self.triggers = events_dict()

		Players.make_players()

		self.operations = {
			# if the client is sending the name of that player
			'@P': lambda info: self.add_player_name(info),

			# if the client is telling us how many cards the game should start with
			'@N': lambda info: self.set_card_number(info),

			# if the client is trying to play a card
			'@C': lambda info: self.execute_play(info[2:4], int(info[4])),

			# if the client is telling us the players are ready to start the game
			'@s': lambda info: self.time_to_start(),

			# if the client is telling us how many tricks_this_round they are going to bid in this round.
			'@B': lambda info: self.player_makes_bid(info),

			# If the client is telling us whether they want an instant rematch after the game has ended.
			'@1': lambda info: self.repeat_question_answer(),

			# If the client is saying they don't want a repeat game.
			'@T': lambda info: KILL_PROGRAMME_MESSAGE,

			# If the client is telling us they've completed an animation sequence.
			'@A': lambda info: self.player_action_completed(info),

			# If it's just a ping to keep the connection going
			'pi': lambda info: DEFAULT_NETWORK_MESSAGE
		}

	@classmethod
	@property
	def players(cls, /) -> type[Players]:
		return Players

	@classmethod
	@property
	def cards(cls, /) -> type[Card]:
		return Card

	@staticmethod
	def add_player_name(info: str, /) -> None:
		Players(int(info[-1])).name = info[2:-1]
		return Players.all_players_named

	def set_card_number(self, number: NumberInput, /) -> None:
		self.start_card_number = int(number)

	def time_to_start(self, /) -> None:
		self._play_started = True

	@staticmethod
	def player_action_completed(info: str, /) -> None:
		Players(int(info[2])).action_complete = True

	@staticmethod
	def player_makes_bid(info: str, /) -> None:
		Players(int(info[4])).bids(int(info[2:4]))

	def repeat_question_answer(self, /) -> None:
		self.repeat_game = True

	def wait_for_players(self, attribute: str) -> None:
		self.triggers[attribute] += 1
		Players.wait_for_players()

	def play_game(self, /) -> None:
		# wait until the opening sequence is full_message_received

		while not self.start_card_number:
			delay(1)

		Players.next_stage()

		self.wait_for_players('game_initialisation')
		self.triggers['StartNumberSet'] += 1

		for cardnumber in range(self.start_card_number, 0, -1):
			self.play_round(cardnumber)

		self.repeat_game = False

		while not self.repeat_game:
			delay(1)

		self.new_game_reset()

		# wait until all players have logged their new player_index.
		self.wait_for_players('new_game_reset')

	def play_round(self, cardnumber: int) -> None:
		# Make a new pack of cards, set the trumpsuit.
		shuffled_pack = Pack.randomly_shuffled()
		self.trump_card = ((TrumpCard := shuffled_pack.pop()),)
		self._trump_suit = (trumpsuit := TrumpCard.Suit)
		self.triggers['new_pack'] += 1

		# Deal cards
		for player in Players:
			player.receives_card([shuffled_pack.pop() for _ in range(cardnumber)], trumpsuit)

		self.wait_for_players('CardsDealt')

		# play tricks_this_round
		for i in range(cardnumber):
			self.play_trick()

		# Reset players for the next round.
		for player in Players:
			player.reset_bid()

		self.end_round()

	def play_trick(self, /) -> None:
		self.wait_for_players('TrickStart')

		for i in range(rc.player_number):
			while len(self.played_cards) == i:
				delay(100)

		Players.next_stage()
		self.wait_for_players('TrickWinnerLogged')
		self.played_cards.clear()
		self.wait_for_players('TrickEnd')

	def client_comms_loop(self, /) -> NoReturn:
		with printing_exc():
			while True:
				if len(Players) != rc.player_number:
					raise Exception('A client appears to have left the game!')

				delay(300)
				self.export()

	def export(self, /) -> None:
		start_no = self.start_card_number

		string = '---'.join((
			'--'.join([f'{v}' for v in self.triggers.values()]),
			Players.export_string(),
			cards_to_string(self.played_cards),
			f'{int(self._play_started)}{int(self.repeat_game)}{start_no}{repr(self.trump_card) if self.trump_card else ""}'
		))

		for player in Players:
			player.schedule_send('---'.join((string, cards_to_string(player.hand))))

	# PlayerNumber is given in the abstract_game repr
	def __repr__(self) -> str:
		return '\n'.join((
			super().__repr__(),
			f'gameplayers = {Players.repr_list}\ntriggers: {self.triggers}'
		))


def cards_to_string(cards_list: list[Card]) -> OptionalStr:
	if not cards_list:
		return 'None'
	return '-'.join([str(card.index_in_pack) for card in cards_list])
