"""One class and two functions to allow for a password to be transmitted securely from client to server."""


from Crypto.Cipher import AES
from Crypto.Util.number import getPrime
from Crypto.Util.Padding import pad, unpad
from string import ascii_letters, digits, punctuation
from secrets import choice


PasswordLength = 32
PrintableCharacters = ''.join((digits, ascii_letters, punctuation))


class PasswordChecker(object):
	"""

	Class to create an AES-encrypted communications channel using the Diffie-Helmann algorithm...
	...And then use that secure communications channel to authenticate an attempted connection...
	 ...by the transfer of a password from the client to the server

	 """

	__slots__ = 'parent', 'PrivateKey', 'server', 'ServerPublicKey', 'ClientPublicKey', 'conn', 'cipher',\
	            'ServerPartialKey', 'ClientPartialKey', 'FullKey'

	def __init__(self, parent, conn, server=False):
		self.parent = parent
		self.PrivateKey = self.GenerateKey()

		self.ServerPublicKey = self.GenerateKey() if server else None
		self.ClientPublicKey = None if server else self.GenerateKey()

		self.conn = conn
		self.server = server
		self.cipher,  = None
		self.ServerPartialKey = None
		self.ClientPartialKey = None
		self.FullKey = None

		print('Exchanging keys...')
		self.ExchangeKeys()

	def ServerChecksPassword(self, conn, password, PasswordLength=PasswordLength):
		# The client sends us the password, encrypted using the full key, and the initialisation vector.
		# The server uses the full key and the initialisation vector to calculate the cipher used to encrypt the password.
		# The server decrypts the password that the client sent it.
		# The client sends back the password, the server checks that it's correct.

		print('Receiving password from client...')
		CipheredPassword = self.parent.SubReceive(PasswordLength + 16, conn)
		iv = self.parent.SubReceive(16, conn)

		print('Checking password...')
		ReceivedPassword = unpad(self.GetCipher(iv).decrypt(CipheredPassword), AES.block_size).decode()

		if ReceivedPassword != password:
			return False

		print('Correct password received.')
		return True

	def ClientSendsPassword(self, password):
		print('Encrypting password...')

		# Use the key to get a cipher, use the cipher to encrypt the password.
		# Send the encrypted password and the iv to the server.
		CipheredPassword = self.GetCipher(None).encrypt(pad(password.encode(), AES.block_size))
		print('Sending password to server...')
		self.conn.sendall(CipheredPassword)
		self.conn.sendall(self.cipher.iv)

	@staticmethod
	def GenerateKey():
		return getPrime(18)

	def ExchangeKeys(self):
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		Partial = False

		if self.server:
			self.SendKey(Partial)
			self.ReceiveKey(Partial)
		else:
			self.ReceiveKey(Partial)
			self.SendKey(Partial)

		self.CalculatePartialKey()

		Partial = True

		if self.server:
			self.SendKey(Partial)
			self.ReceiveKey(Partial)
		else:
			self.ReceiveKey(Partial)
			self.SendKey(Partial)

		self.CalculateFullKey()
		print('Completed key exchange.')

	def SendKey(self, Partial):
		if self.server:
			key = self.ServerPartialKey if Partial else self.ServerPublicKey
		else:
			key = self.ClientPartialKey if Partial else self.ClientPublicKey

		key = str(key)

		if Partial:
			key = f"{key}{''.join(('-' for i in range(10 - len(key))))}"

		self.conn.sendall(key.encode())

	def ReceiveKey(self, Partial):
		Key = self.parent.SubReceive((10 if Partial else 6), self.conn).decode()

		if Partial:
			Key = Key.split('-')[0]

		Key = int(Key)

		if self.server and Partial:
			self.ClientPartialKey = Key
		elif self.server:
			self.ClientPublicKey = Key
		elif Partial:
			self.ServerPartialKey = Key
		else:
			self.ServerPublicKey = Key

	def CalculatePartialKey(self):
		PartialKey = (self.ServerPublicKey ** self.PrivateKey) % self.ClientPublicKey

		if self.server:
			self.ServerPartialKey = PartialKey
		else:
			self.ClientPartialKey = PartialKey

	def CalculateFullKey(self):
		PartialKey = self.ClientPartialKey if self.server else self.ServerPartialKey
		self.FullKey = hex(((PartialKey ** self.PrivateKey) % self.ClientPublicKey) ** 5)[:16]

	def GetCipher(self, iv):
		self.cipher = AES.new(self.FullKey.encode(), AES.MODE_CBC, iv)
		return self.cipher


def GeneratePassword(PasswordLength=PasswordLength, PrintableCharacters=PrintableCharacters):
	"""Function to generate a random hexademical token, to be used as a password"""

	return ''.join(choice(PrintableCharacters) for i in range(PasswordLength))


def PasswordInput(text, PasswordLength=PasswordLength):
	"""Function for validating a password that has been inputted by the user"""

	if not text:
		return None

	assert len(text) == PasswordLength, f'Password must be a hexadecimal string of exactly {PasswordLength} characters.'
