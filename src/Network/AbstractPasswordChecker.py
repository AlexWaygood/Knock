"""One class and two functions to allow for a password to be transmitted securely from client to server."""

from src.DataStructures import DictLike
from src.PrintableCharacters import PrintableCharacters
from Crypto.Cipher import AES
from Crypto.Util.number import getPrime
from secrets import choice


PasswordLength = 32


class PasswordChecker(DictLike):
	"""

	Class to create an AES-encrypted communications channel using the Diffie-Helmann algorithm...
	...And then use that secure communications channel to authenticate an attempted connection...
	 ...by the transfer of a password from the client to the server

	 """

	__slots__ = 'parent', 'PrivateKey', 'ServerPublicKey', 'ClientPublicKey', 'conn', 'cipher',\
	            'ServerPartialKey', 'ClientPartialKey', 'FullKey'

	def __init__(self, parent, conn, *args, **kwargs):
		"""
		@type parent: src.Network.AbstractNetwork.Network
		@type conn: socket.socket
		"""

		self.parent = parent
		self.PrivateKey = self.GenerateKey()
		self.GeneratePublicKeys()
		self.conn = conn
		self.cipher = None
		self.ServerPartialKey = None
		self.ClientPartialKey = None
		self.FullKey = None

		print('Exchanging keys...')
		self.ExchangeKeys()

	# Placeholder method, to be overriden higher up the inheritance chain
	def GeneratePublicKeys(self):
		pass

	@staticmethod
	def GenerateKey():
		return getPrime(18)

	# Another placeholder method
	def ExchangeKeys(self):
		pass

	def SendKey(self, Partial: bool, server: bool):
		key = str(self[f'{"Server" if server else "Client"}{"Partial" if Partial else "Public"}Key'])

		if Partial:
			key = f"{key}{''.join(('-' for _ in range(10 - len(key))))}"

		self.conn.sendall(key.encode())

	def ReceiveKey(self, Partial: bool):
		Key = self.parent.SubReceive((10 if Partial else 6), self.conn).decode()

		if Partial:
			Key = Key.split('-')[0]

		return int(Key)

	def CalculatePartialKey(self):
		return (self.ServerPublicKey ** self.PrivateKey) % self.ClientPublicKey

	def CalculateFullKey(self, server: bool):
		PartialKey = self.ClientPartialKey if server else self.ServerPartialKey
		self.FullKey = hex(((PartialKey ** self.PrivateKey) % self.ClientPublicKey) ** 5)[:16]

	def GetCipher(self, iv):
		self.cipher = AES.new(self.FullKey.encode(), AES.MODE_CBC, iv)
		return self.cipher


def GeneratePassword(PasswordLength=PasswordLength, PrintableCharacters=PrintableCharacters):
	"""Function to generate a random hexademical token, to be used as a password

	@type PasswordLength: int
	@type PrintableCharacters: str
	"""

	return ''.join(choice(PrintableCharacters) for _ in range(PasswordLength))


def PasswordInput(text, PasswordLength=PasswordLength):
	"""Function for validating a password that has been inputted by the user

	@type text: str
	@type PasswordLength: int
	"""

	if not text:
		return None

	assert len(text) == PasswordLength, f'Password must be a hexadecimal string of exactly {PasswordLength} characters.'
