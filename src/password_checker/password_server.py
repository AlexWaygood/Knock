from __future__ import annotations
from typing import TYPE_CHECKING
from logging import getLogger

# noinspection PyPackageRequirements
from Crypto.Util.Padding import unpad
# noinspection PyPackageRequirements
from Crypto.Cipher.AES import block_size as AES_block_size

from src.password_checker.password_abstract import PasswordChecker

if TYPE_CHECKING:
	from socket import socket
	from src.network.network_server import Server


log = getLogger(__name__)


# noinspection PyAttributeOutsideInit
class ServerPasswordChecker(PasswordChecker):
	password = ''

	def __init__(self,
	             parent: Server,
	             conn: socket):

		super().__init__(parent, conn)
		self.ServerPublicKey = self.GenerateKey()
		self.ClientPublicKey = None
		self.type = self.Server_type

		log.debug('Exchanging keys...')
		print('Exchanging keys...')

		self.ExchangeKeys()

	def CheckPassword(self) -> bool:
		# The client sends us the password, encrypted using the full key, and the initialisation vector.
		# The server uses the full key and the initialisation vector to calculate the cipher used to encrypt the password.
		# The server decrypts the password that the client sent it.
		# The client sends back the password, the server checks that it's correct.

		print('Receiving password from client...')
		log.debug('Receiving password from client...')

		CipheredPassword = self.parent.SubReceive(self.PasswordLength + 16, self.conn)
		iv = self.parent.SubReceive(16, self.conn)

		print('Checking password...')
		log.debug('Checking password...')

		ReceivedPassword = unpad(self.GetCipher(iv).decrypt(CipheredPassword), AES_block_size).decode()

		if ReceivedPassword != self.password:
			return False

		print('Correct password received.')
		log.debug('Correct password received.')

		return True

	def ExchangeKeys(self) -> None:
		# The two sides exchange public keys.
		# Both sides calculate a partial key using the two public keys, and their private key.
		# The two sides exchange partial keys.
		# The two sides use the partial keys, combined with their private keys, to calculate the full key on both sides.

		self.SendKey(server=True, Partial=False)
		self.ReceiveKey(Partial=False)
		self.ServerPartialKey = self.CalculatePartialKey()
		self.SendKey(server=True, Partial=True)
		self.ReceiveKey(Partial=True)
		self.CalculateFullKey(server=True)

		print('Completed key exchange.')
		log.debug('Completed key exchange.')
