"""Abstractions for the rest of the `cards` module."""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
from aenum import EnumMeta, Enum, OrderedEnum
from functools import cache
from src import DocumentedMetaclassMixin


class CardClassEnumMeta(DocumentedMetaclassMixin, EnumMeta, ABCMeta):
	"""Metaclass for `CardClassEnum`."""


class CardClassEnum(Enum, metaclass=CardClassEnumMeta):
	"""Abstract base class for the `Rank`, `Suit`, `ServerCard` and `ClientCard` enums.

	The `Rank`, `Suit`, `ServerCard` and `ClientCard` enums have the following properties:
		-   Custom `__str__` and `__repr__` methods.
		-   Members within an enum all have values of the same type (though this is not enforced).
		-   Members cannot be compared to objects of a different type.
		-   Members can be accessed programmatically via multiple names
		-   Members have `concise_name` and `verbose_name` properties,
			which can be accessed through a custom `__format__` method.
	"""

	# We DO NOT add ordering methods here,
	# as it makes no sense for Cards to be compared to each other
	# without knowing the trumpsuit for that round.

	@property
	@abstractmethod
	def concise_name(self, /) -> str:
		"""Return a concise name for the enum member."""

	@property
	@abstractmethod
	def verbose_name(self, /) -> str:
		"""Return a verbose name for the enum member."""

	@cache
	def __repr__(self, /) -> str:
		return f'{self.__class__.__name__}({self.concise_name})'

	def __str__(self, /) -> str:
		return repr(self)

	@cache
	def __format__(self, format_spec: str, /) -> str:
		"""Return the concise name for the specifier 'c' or 'concise', and the verbose name for 'v' or 'verbose."""

		if format_spec == 'concise':
			return self.concise_name
		if format_spec == 'verbose':
			return self.verbose_name
		return super().__format__(format_spec)


# noinspection PyAbstractClass
class SuitOrRankEnum(CardClassEnum, OrderedEnum):
	"""Suit and Rank are ordered."""
