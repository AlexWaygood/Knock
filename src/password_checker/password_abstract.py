"""One class and two functions to allow for a password to be transmitted securely from client to server."""

from __future__ import annotations
from typing import TYPE_CHECKING
from secrets import choice

# noinspection PyPackageRequirements,PyPep8Naming
from Crypto.Cipher.AES import MODE_CBC, new as AES_new

from src import DictLike
from src.static_constants import StringConstants
from src.secret_passwords import PASSWORD_LENGTH, PRIME_N

if TYPE_CHECKING:
	from src.special_knock_types import OptionalBytes, OptionalCipherType, OptionalInt, OptionalStr
	from src.network.network_abstract import Network
	from socket import socket
	# noinspection PyProtectedMember,PyPackageRequirements
	from Crypto.Cipher._mode_cbc import CbcMode as CipherType
	# noinspection PyPackageRequirements
	from Crypto.Util.number import getPrime


SERVER_TYPE = 'Server'
CLIENT_TYPE = 'Client'


def key_maker() -> int:
	return getPrime(PRIME_N)


def make_cipher(full_key: str, iv: OptionalBytes) -> CipherType:
	return AES_new(full_key.encode(), MODE_CBC, iv)


def generate_password() -> str:
	"""Function to generate a random hexademical token, to be used as a password"""
	return ''.join(choice(StringConstants.PRINTABLE_CHARACTERS) for _ in range(PASSWORD_LENGTH))


class IncorrectPasswordLengthException(ValueError):
	"""Exception raised if the client inputs a password of an incorrect length."""


def validate_inputted_password(inputted_password: str) -> None:
	"""Raise `IncorrectPasswordLengthException` if the client has inputted a password of the wrong length."""

	if inputted_password and (len(inputted_password) != PASSWORD_LENGTH):
		raise IncorrectPasswordLengthException(
			f'Password must be a hexadecimal string of exactly {PASSWORD_LENGTH} characters.'
		)


class PasswordChecker(DictLike):
	"""

	Class to create an AES-encrypted communications channel using the Diffie-Helmann algorithm...
	...And then use that secure communications channel to authenticate an attempted connection...
	...by the transfer of a password from the client to the server
	"""

	__slots__ = (
		'parent', 'PrivateKey', 'server_public_key', 'client_public_key', 'conn', 'cipher', 'ServerPartialKey',
		'ClientPartialKey', 'FullKey', 'type'
	)

	Server_type = SERVER_TYPE
	Client_type = CLIENT_TYPE
	PasswordLength = PASSWORD_LENGTH

	def __init__(
			self,
			parent: Network,
			conn: socket,
			*args,
			**kwargs
	) -> None:

		self.parent = parent
		self.PrivateKey = self.generate_key()
		self.conn = conn
		self.cipher: OptionalCipherType = None
		self.ServerPartialKey: OptionalInt = None
		self.ClientPartialKey: OptionalInt = None
		self.FullKey: OptionalStr = None

	@staticmethod
	def generate_key() -> int:
		"""
		Will generate a prime number of a certain length,
		depending on the settings specified in secret_passwords.py
		"""

		return key_maker()

	def send_key(self, /, *, partial: bool, server: bool) -> None:
		key = str(self[f'{self.Server_type if server else self.Client_type}{"partial" if partial else "Public"}Key'])

		if partial:
			key = f"{key}{''.join(('-' for _ in range(10 - len(key))))}"

		self.conn.sendall(key.encode())

	def receive_key(self, /, *, partial: bool) -> None:
		key = self.parent.sub_receive((10 if partial else 6), self.conn).decode()

		if partial:
			key = key.split('-')[0]

		self[f'{self.type}{"partial" if partial else "Public"}Key'] = key

	def calculate_partial_key(self, /) -> float:
		return (self.server_public_key ** self.PrivateKey) % self.client_public_key

	def calculate_full_key(self, /, *, server: bool) -> None:
		partial_key = self.ClientPartialKey if server else self.ServerPartialKey
		self.FullKey = hex(((partial_key ** self.PrivateKey) % self.client_public_key) ** 5)[:16]

	def get_cipher(self, iv: OptionalBytes) -> CipherType:
		self.cipher = make_cipher(self.FullKey, iv)
		return self.cipher
