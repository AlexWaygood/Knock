from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

# noinspection PyPackageRequirements
from Crypto.Util.Padding import unpad
# noinspection PyPackageRequirements,PyPep8Naming
from Crypto.Cipher.AES import block_size as AES_block_size

from src.password_checker import PasswordChecker

if TYPE_CHECKING:
	from socket import socket
	from src.network.network_server import Server


log = getLogger(__name__)


# noinspection PyAttributeOutsideInit
class ServerPasswordChecker(PasswordChecker):
	password = ''

	def __init__(self, parent: Server, conn: socket) -> None:
		super().__init__(parent, conn)
		self.ServerPublicKey = self.generate_key()
		self.ClientPublicKey = None
		self.type = self.Server_type

		log.debug('Exchanging keys...')
		print('Exchanging keys...')

		self.exchange_keys()

	def check_password(self, /) -> bool:
		# The client sends us the password, encrypted using the full key, and the initialisation vector.
		# The server uses the full key and the initialisation vector to calculate the cipher used to encrypt the password.
		# The server decrypts the password that the client sent it.
		# The client sends back the password, the server checks that it's correct.

		print('Receiving password from client...')
		log.debug('Receiving password from client...')

		ciphered_password = self.parent.sub_receive(self.PasswordLength + 16, self.conn)
		iv = self.parent.sub_receive(16, self.conn)

		print('Checking password...')
		log.debug('Checking password...')

		received_password = unpad(self.get_cipher(iv).decrypt(ciphered_password), AES_block_size).decode()

		if received_password != self.password:
			return False

		print('Correct password received.')
		log.debug('Correct password received.')

		return True

	def exchange_keys(self, /) -> None:
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		self.send_key(server=True, partial=False)
		self.receive_key(partial=False)
		self.ServerPartialKey = self.calculate_partial_key()
		self.send_key(server=True, partial=True)
		self.receive_key(partial=True)
		self.calculate_full_key(server=True)

		print('Completed key exchange.')
		log.debug('Completed key exchange.')
