from typing import Sequence


class DictLike:
	__slots__ = tuple()

	def __getitem__(self, item: str):
		return getattr(self, item)

	def __setitem__(self, key: str, value):
		setattr(self, key, value)

	def GetAttributes(self, attrs: Sequence[str]):
		return [self[attr] for attr in attrs]


class OnlyAFixedNumber:
	__slots__ = tuple()

	AllOfKind = {}

	def __new__(cls, *args, **kwargs):
		try:
			return cls.AllOfKind[args if len(args) > 1 else args[0]]
		except:
			new = object.__new__(cls)
			cls.AllOfKind[args if len(args) > 1 else args[0]] = new
			return new
