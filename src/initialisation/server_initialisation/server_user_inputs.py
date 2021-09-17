from __future__ import annotations
from pyinputplus import inputInt, inputMenu, inputCustom, inputYesNo
from src.password_checker.password_abstract import generate_password, validate_inputted_password
from src.static_constants import CLASSIC_BIDDING_SYSTEM, RANDOM_BIDDING_SYSTEM


MIN_PLAYERS = 2
MAX_PLAYERS = 6


def user_inputs() -> tuple[int, str, str, bool]:
	number_of_players = inputInt('How many players will be playing? ', min=MIN_PLAYERS, max=MAX_PLAYERS)
	print()

	bidding_rule_choices = [
		'Classic rules (players decide what they will bid prior to each round)',
		'Anna Benjer rules (bids are randomly generated for each player prior to each round)'
	]

	bidding_system = inputMenu(
		choices=bidding_rule_choices,
		prompt='Which variant of the rules will this tournament use?\n\n',
		numbered=True,
		blank=True
	)

	bidding_system = RANDOM_BIDDING_SYSTEM if bidding_system == bidding_rule_choices[1] else CLASSIC_BIDDING_SYSTEM
	print()

	password_choices = [
		"I want a new, randomly generated password for this game",
		"I've already got a password for this game",
		"I don't want a password for this game"
	]

	choice = inputMenu(
		choices=password_choices,
		prompt='Select whether you want to set a password for this game:\n\n',
		numbered=True,
		blank=True
	)

	if choice == password_choices[0]:
		password = generate_password()
		print(f'\nYour randomly generated password for this session is {password}')
	elif choice == password_choices[1]:
		password = inputCustom(validate_inputted_password, '\nPlease enter the password for this session: ')
	else:
		password = ''

	print()

	manually_verify = inputYesNo(
		'\nDo you want to manually authorise each connection? '
		'(If "no", new connections will be accepted automatically if they have entered the correct password.) ',
		blank=True
	)

	return number_of_players, bidding_system, password, manually_verify
