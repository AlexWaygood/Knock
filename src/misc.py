from __future__ import annotations

from time import strftime, localtime
from typing import Any, Sequence, Union
from logging import Logger, getLogger


def GetDate() -> str:
	return strftime("%d-%m-%Y", localtime())


class DictLike:
	__slots__ = tuple()

	def __getitem__(self, item: str) -> Any:
		return getattr(self, item)

	def __setitem__(
			self,
			key: str,
			value: Any
	) -> None:
		setattr(self, key, value)

	def GetAttributes(self, attrs: Sequence[str]) -> Sequence[Any]:
		return [self[attr] for attr in attrs]


class Log:
	def debug(self, *args, **kwargs) -> None:
		pass


def GetLogger(FrozenState: bool) -> Union[Log, Logger]:
	return Log() if FrozenState else getLogger(__name__)
