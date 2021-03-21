from socket import gethostbyname
from pyinputplus import inputCustom, inputMenu
from ipaddress import ip_address
from src.password_checker.password_abstract import PasswordInput


def IPValidation(InputText: str):
	"""Will raise an exception if the user has not entered a valid IP or hostname to connect to."""

	try:
		ip_address(InputText)
	except:
		address = gethostbyname(InputText)
		ip_address(address)

	return InputText


def UserInputs():
	# IP = 'alexknockparty.mywire.org'
	IP = '127.0.0.1'
	print('Connecting to local host.')
	Port = 5555
	# IP = inputCustom(IPValidation, 'Please enter the IP address or hostname of the server you want to connect to: ')
	# Port = inputInt('Please enter which port you wish to connect to: ', min=5000, max=65535)

	password = inputCustom(
		PasswordInput,
		'Please enter the password to connect to this game, if one has been set (press Enter if none has been set): ',
		blank=True
	)

	ThemeChoices = ['Classic theme (dark red board)', 'High contrast theme (orange board)']
	ThemeDict = {'Classic theme (dark red board)': 'Classic', 'High contrast theme (orange board)': 'Contrast'}

	Theme = inputMenu(
		choices=ThemeChoices,
		prompt='Please select the colour theme you would like to play with:\n\n',
		numbered=True
	)

	return IP, Port, password, ThemeDict[Theme]
