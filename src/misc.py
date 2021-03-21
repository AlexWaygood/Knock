from string import ascii_letters, digits, punctuation
from time import strftime, localtime
from typing import Any, Sequence
from logging import getLogger

PrintableCharacters = ''.join((digits, ascii_letters, punctuation))
PrintableCharactersPlusSpace = PrintableCharacters + ' '


def GetDate():
	return strftime("%d-%m-%Y", localtime())


class DictLike:
	__slots__ = tuple()

	def __getitem__(self, item: str):
		return getattr(self, item)

	def __setitem__(
			self,
			key: str,
			value: Any
	):
		setattr(self, key, value)

	def GetAttributes(self, attrs: Sequence[str]):
		return [self[attr] for attr in attrs]


class Log:
	def debug(self, *args, **kwargs):
		pass


def GetLogger(FrozenState: bool):
	return Log() if FrozenState else getLogger(__name__)
