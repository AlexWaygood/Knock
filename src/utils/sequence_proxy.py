"""A `SequenceProxy` class -- similar in concept to `MappingProxyType`, but for sequences rather than mappings.
Used by the `PlayersMeta` metaclass in `src.players.players_abstract.py`.
"""

import collections.abc
from typing import TypeVar, Sequence, Generic, Iterator, Any

T = TypeVar('T')


# We don't inherit from collections.abc.Sequence directly,
# because we can implement more optimised versions
# of the generic methods that "come for free" with collections.abc.Sequence.

@collections.abc.Sequence.register
class SequenceProxy(Generic[T]):
	"""Read-only proxy for a sequence.
	Similar in concept to `MappingProxyType`, but for sequences rather than mappings.
	"""

	__slots__ = '_sequence'

	def __init__(self, initsequence: Sequence[T]) -> None:
		self._sequence = initsequence

	def __iter__(self) -> Iterator[T]:
		return iter(self._sequence)

	def __getitem__(self, index: int) -> T:
		return self._sequence[index]

	def __len__(self) -> int:
		return len(self._sequence)

	def __contains__(self, item: Any) -> bool:
		return item in self._sequence

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}({self._sequence!r})'

	def __str__(self) -> str:
		return str(self._sequence)

	__reversed__ = collections.abc.Sequence.__reversed__

	def index(self, value: Any, start: int = 0, stop: int = 9223372036854775807) -> int:
		"""Return the index of a value in the underlying sequence."""
		return self._sequence.index(value, start, stop)

	def count(self, value: Any) -> int:
		"""Return the number of times a value appears in the sequence."""
		return self._sequence.count(value)
