from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
from src.Network.AbstractPasswordChecker import PasswordChecker


# noinspection PyAttributeOutsideInit
class ClientPasswordChecker(PasswordChecker):
	def __init__(self, parent, conn, password):
		"""
		@type parent: src.Network.ClientClass.Client
		@type conn: socket.socket
		@type password: str
		"""

		super().__init__(parent, conn)

		# Now that the keys have been exchanged, send the password to the server
		print('Encrypting password...')

		# Use the key to get a cipher, use the cipher to encrypt the password.
		# Send the encrypted password and the iv to the server.
		CipheredPassword = self.GetCipher(None).encrypt(pad(password.encode(), AES.block_size))
		print('Sending password to server...')
		self.conn.sendall(CipheredPassword)
		self.conn.sendall(self.cipher.iv)

	def GeneratePublicKeys(self):
		self.ServerPublicKey = None
		self.ClientPublicKey = self.GenerateKey()

	def ExchangeKeys(self):
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		self.ReceiveKey(Partial=False)
		self.SendKey(server=False, Partial=False)
		self.CalculatePartialKey()
		self.ReceiveKey(Partial=True)
		self.SendKey(server=False, Partial=True)
		self.CalculateFullKey(server=False)
		print('Completed key exchange.')

	def ReceiveKey(self, Partial: bool):
		Key = super().ReceiveKey(Partial)
		self[f'Server{"Partial" if Partial else "Public"}Key'] = Key

	def CalculatePartialKey(self):
		self.ClientPartialKey = super().ClientPartialKey()
