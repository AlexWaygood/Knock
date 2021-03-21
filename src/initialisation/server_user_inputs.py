from pyinputplus import inputInt, inputMenu, inputCustom, inputYesNo
from src.password_checker.password_abstract import GeneratePassword, PasswordInput


def UserInputs():
	NumberOfPlayers = inputInt('How many players will be playing? ', min=2, max=6)
	print()

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

	return NumberOfPlayers, BiddingSystem, password, ManuallyVerify
