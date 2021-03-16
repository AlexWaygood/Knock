"""One class and two functions to allow for a password to be transmitted securely from client to server."""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from secrets import choice

from Crypto.Cipher.AES import MODE_CBC, new as AES_new
from Crypto.Util.number import getPrime

from src.data_structures import DictLike
from src.Misc_locals import PrintableCharacters

if TYPE_CHECKING:
	from src.network.network_abstract_class import Network
	from socket import socket
	# noinspection PyProtectedMember
	from Crypto.Cipher._mode_cbc import CbcMode as CipherType


PasswordLength = 32


class PasswordChecker(DictLike):
	"""

	Class to create an AES-encrypted communications channel using the Diffie-Helmann algorithm...
	...And then use that secure communications channel to authenticate an attempted connection...
	 ...by the transfer of a password from the client to the server

	 """

	__slots__ = 'parent', 'PrivateKey', 'ServerPublicKey', 'ClientPublicKey', 'conn', 'cipher',\
	            'ServerPartialKey', 'ClientPartialKey', 'FullKey', 'type'

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
		self.cipher: Optional[CipherType] = None
		self.ServerPartialKey: Optional[int] = None
		self.ClientPartialKey: Optional[int] = None
		self.FullKey: Optional[str] = None

	@staticmethod
	def GenerateKey():
		return getPrime(18)

	def SendKey(
			self,
			Partial: bool,
			server: bool
	):

		key = str(self[f'{"Server" if server else "Client"}{"Partial" if Partial else "Public"}Key'])

		if Partial:
			key = f"{key}{''.join(('-' for _ in range(10 - len(key))))}"

		self.conn.sendall(key.encode())

	def ReceiveKey(self, Partial: bool):
		Key = self.parent.SubReceive((10 if Partial else 6), self.conn).decode()

		if Partial:
			Key = Key.split('-')[0]

		self[f'{self.type}{"Partial" if Partial else "Public"}Key'] = Key

	def CalculatePartialKey(self):
		return (self.ServerPublicKey ** self.PrivateKey) % self.ClientPublicKey

	def CalculateFullKey(self, server: bool):
		PartialKey = self.ClientPartialKey if server else self.ServerPartialKey
		self.FullKey = hex(((PartialKey ** self.PrivateKey) % self.ClientPublicKey) ** 5)[:16]

	def GetCipher(self, iv: Optional[bytes]):
		self.cipher: CipherType = AES_new(self.FullKey.encode(), MODE_CBC, iv)
		return self.cipher


def GeneratePassword(PasswordLength: int = PasswordLength,
                     PrintableCharacters: str = PrintableCharacters):

	"""Function to generate a random hexademical token, to be used as a password"""
	return ''.join(choice(PrintableCharacters) for _ in range(PasswordLength))


def PasswordInput(text: str,
                  PasswordLength: int = PasswordLength):

	"""Function for validating a password that has been inputted by the user"""

	if not text:
		return None

	assert len(text) == PasswordLength, f'Password must be a hexadecimal string of exactly {PasswordLength} characters.'
