from __future__ import annotations
from typing import TYPE_CHECKING

# noinspection PyPackageRequirements
from Crypto.Util.Padding import pad
# noinspection PyPackageRequirements,PyPep8Naming
from Crypto.Cipher.AES import block_size as AES_block_size

from src.password_checker import PasswordChecker

if TYPE_CHECKING:
	from src.network.network_client import Client
	from socket import socket


# noinspection PyAttributeOutsideInit
class ClientPasswordChecker(PasswordChecker):
	def __init__(self, parent: Client, conn: socket, password: str) -> None:
		super().__init__(parent, conn)
		self.server_public_key = None
		self.client_public_key = self.generate_key()
		self.type = self.Client_type
		print('Exchanging keys...')
		self.exchange_keys()

		# Now that the keys have been exchanged, send the password to the server
		print('Encrypting password...')

		# Use the key to get a cipher, use the cipher to encrypt the password.
		# Send the encrypted password and the iv to the server.
		ciphered_password = self.get_cipher(None).encrypt(pad(password.encode(), AES_block_size))
		print('Sending password to server...')
		self.conn.sendall(ciphered_password)
		self.conn.sendall(self.cipher.iv)

	def exchange_keys(self) -> None:
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		self.receive_key(partial=False)
		self.send_key(server=False, partial=False)
		self.ClientPartialKey = self.calculate_partial_key()
		self.receive_key(partial=True)
		self.send_key(server=False, partial=True)
		self.calculate_full_key(server=False)
		print('Completed key exchange.')
