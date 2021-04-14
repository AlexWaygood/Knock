"""One class and two functions to allow for a password to be transmitted securely from client to server."""

from __future__ import annotations
from typing import TYPE_CHECKING
from secrets import choice

# noinspection PyPackageRequirements
from Crypto.Cipher.AES import MODE_CBC, new as AES_new
# noinspection PyPackageRequirements
from Crypto.Util.number import getPrime

from src.misc import DictLike
from src.global_constants import PRINTABLE_CHARACTERS

if TYPE_CHECKING:
	from src.special_knock_types import OptionalBytes, OptionalCipherType, OptionalInt, OptionalStr
	from src.network.network_abstract import Network
	from socket import socket
	# noinspection PyProtectedMember,PyPackageRequirements
	from Crypto.Cipher._mode_cbc import CbcMode as CipherType


PASSWORD_LENGTH = 32
SERVER_TYPE = 'Server'
CLIENT_TYPE = 'Client'


def KeyMaker() -> int:
	return getPrime(18)


def MakeCipher(FullKey: str, iv: OptionalBytes) -> CipherType:
	return AES_new(FullKey.encode(), MODE_CBC, iv)


def GeneratePassword() -> str:
	"""Function to generate a random hexademical token, to be used as a password"""
	return ''.join(choice(PRINTABLE_CHARACTERS) for _ in range(PASSWORD_LENGTH))


def PasswordInput(text: str):
	"""Function for validating a password that has been inputted by the user"""

	if not text:
		return None

	assert len(text) == PASSWORD_LENGTH, f'Password must be a hexadecimal string of exactly {PASSWORD_LENGTH} characters.'


class PasswordChecker(DictLike):
	"""

	Class to create an AES-encrypted communications channel using the Diffie-Helmann algorithm...
	...And then use that secure communications channel to authenticate an attempted connection...
	 ...by the transfer of a password from the client to the server

	 """

	__slots__ = 'parent', 'PrivateKey', 'ServerPublicKey', 'ClientPublicKey', 'conn', 'cipher',\
	            'ServerPartialKey', 'ClientPartialKey', 'FullKey', 'type'

	Server_type = SERVER_TYPE
	Client_type = CLIENT_TYPE
	PasswordLength = PASSWORD_LENGTH

	def __init__(
			self,
			parent: Network,
			conn: socket,
			*args,
			**kwargs
	):

		self.parent = parent
		self.PrivateKey = self.GenerateKey()
		self.conn = conn
		self.cipher: OptionalCipherType = None
		self.ServerPartialKey: OptionalInt = None
		self.ClientPartialKey: OptionalInt = None
		self.FullKey: OptionalStr = None

	@staticmethod
	def GenerateKey() -> int:
		return KeyMaker()

	def SendKey(
			self,
			Partial: bool,
			server: bool
	):

		key = str(self[f'{self.Server_type if server else self.Client_type}{"Partial" if Partial else "Public"}Key'])

		if Partial:
			key = f"{key}{''.join(('-' for _ in range(10 - len(key))))}"

		self.conn.sendall(key.encode())

	def ReceiveKey(self, Partial: bool):
		Key = self.parent.SubReceive((10 if Partial else 6), self.conn).decode()

		if Partial:
			Key = Key.split('-')[0]

		self[f'{self.type}{"Partial" if Partial else "Public"}Key'] = Key

	def CalculatePartialKey(self) -> float:
		return (self.ServerPublicKey ** self.PrivateKey) % self.ClientPublicKey

	def CalculateFullKey(self, server: bool):
		PartialKey = self.ClientPartialKey if server else self.ServerPartialKey
		self.FullKey = hex(((PartialKey ** self.PrivateKey) % self.ClientPublicKey) ** 5)[:16]

	def GetCipher(self, iv: OptionalBytes):
		self.cipher = MakeCipher(self.FullKey, iv)
		return self.cipher
