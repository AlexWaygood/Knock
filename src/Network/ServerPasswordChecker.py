from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES
from src.Network.AbstractPasswordChecker import PasswordChecker, PasswordLength


# noinspection PyAttributeOutsideInit
class ServerPasswordChecker(PasswordChecker):
	def GeneratePublicKeys(self):
		self.ServerPublicKey = self.GenerateKey()
		self.ClientPublicKey = None

	def CheckPassword(self, conn, password, PasswordLength=PasswordLength):
		"""
		@type conn: socket.socket
		@type password: str
		@type PasswordLength: int
		"""

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

	def ExchangeKeys(self):
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		self.SendKey(server=True, Partial=False)
		self.ReceiveKey(Partial=False)
		self.CalculatePartialKey()
		self.SendKey(server=True, Partial=True)
		self.ReceiveKey(Partial=True)
		self.CalculateFullKey(server=True)
		print('Completed key exchange.')

	def ReceiveKey(self, Partial):
		Key = super().ReceiveKey(Partial)
		self[f'Client{"Partial" if Partial else "Public"}Key'] = Key

	def CalculatePartialKey(self):
		self.ServerPartialKey = super().CalculatePartialKey()
