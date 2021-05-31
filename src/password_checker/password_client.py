from __future__ import annotations
from typing import TYPE_CHECKING

# noinspection PyPackageRequirements
from Crypto.Util.Padding import pad
# noinspection PyPackageRequirements
from Crypto.Cipher.AES import block_size as AES_block_size

from src.password_checker.password_abstract import PasswordChecker

if TYPE_CHECKING:
	from src.network.network_client import Client
	from socket import socket


# noinspection PyAttributeOutsideInit
class ClientPasswordChecker(PasswordChecker):
	def __init__(
			self,
			parent: Client,
			conn: socket,
			password: str
	) -> None:

		super().__init__(parent, conn)
		self.ServerPublicKey = None
		self.ClientPublicKey = self.GenerateKey()
		self.type = self.Client_type
		print('Exchanging keys...')
		self.ExchangeKeys()

		# Now that the keys have been exchanged, send the password to the server
		print('Encrypting password...')

		# Use the key to get a cipher, use the cipher to encrypt the password.
		# Send the encrypted password and the iv to the server.
		CipheredPassword = self.GetCipher(None).encrypt(pad(password.encode(), AES_block_size))
		print('Sending password to server...')
		self.conn.sendall(CipheredPassword)
		self.conn.sendall(self.cipher.iv)

	def ExchangeKeys(self) -> None:
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		self.ReceiveKey(Partial=False)
		self.SendKey(server=False, Partial=False)
		self.ClientPartialKey = self.CalculatePartialKey()
		self.ReceiveKey(Partial=True)
		self.SendKey(server=False, Partial=True)
		self.CalculateFullKey(server=False)
		print('Completed key exchange.')
