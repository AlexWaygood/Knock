"""A series of lies to make the type-checker happy."""

from abc import abstractmethod
from enum import Enum, IntEnum, EnumMeta
from typing import ClassVar, final, Sequence, Any, NamedTuple, TypeVar, Callable, Iterator
# noinspection PyUnresolvedReferences
from functools import singledispatchmethod, cache

class StrEnum(Enum): ...
class DocumentedPlaceholdersMeta(EnumMeta): ...
class DocumentedPlaceholders(Enum, metaclass=EnumMeta): ...
class DocumentedConstants(Enum): ...
class FrozenError(AttributeError): ...
class FrozenInstanceError(FrozenError): ...
class FrozenClassError(FrozenError): ...
class IntEnumNiceStr(IntEnum): ...
cached_readonly_property = property


class DocumentedEnum(Enum):
	# noinspection PyMethodOverriding
	@staticmethod
	def _generate_next_value_(number_so_far: Iterator[int] = ...) -> Any: ...


AnyFunction = Callable[..., Any]


# noinspection PyPep8Naming
class abstract_classmethod(classmethod):
	def __init__(self, func: AnyFunction) -> None:
		super().__init__(abstractmethod(func))


# noinspection PyPep8Naming
class classmethod_property(property):
	def __init__(self, fget: AnyFunction) -> None:
		super().__init__(fget=classmethod(fget))


# noinspection PyPep8Naming
class cached_classmethod_property(property):
	def __init__(self, fget: AnyFunction) -> None:
		super().__init__(fget=classmethod(cache(fget)))


# noinspection PyPep8Naming
class abstract_classmethod_property(property):
	def __init__(self, fget: AnyFunction) -> None:
		super().__init__(fget=classmethod(abstractmethod(fget)))

def get_date() -> str: ...

class DataclassyReprBase:
	__slots__ = ()
	NON_REPR_SLOTS: ClassVar[frozenset[str]]
	EXTRA_REPR_ATTRS: ClassVar[tuple[str]]

	@final
	@cached_readonly_property
	def _repr_attrs(self, /) -> Sequence[str]: ...

	@final
	def __repr__(self, /) -> str: ...

class DictLike:
	__slots__ = tuple()
	def __getitem__(self, item: str) -> Any: ...
	def __setitem__(self, key: str, value: Any) -> None: ...
	def get_attributes(self, attrs: Sequence[str]) -> Sequence[Any]: ...

P = TypeVar('P', bound='Position')
class Position(NamedTuple):
	x: float
	y: float
	def __rshift__(self: P, other: [float, float]) -> P: ...
	__irshift__ = __rshift__
	def replace(self: P, /, *, x: float, y: float) -> P: ...
	def replace_x(self: P, /, *, x: float) -> P: ...
	def replace_y(self: P, /, *, y: float) -> P: ...


class Vector(NamedTuple):
	x_motion: float
	y_motion: float


class Dimensions(NamedTuple):
	width: float
	height: float


class ConnectionAddress(NamedTuple):
	IP: str
	port: int

class DocumentedMetaclassMixin(type):
	__slots__ = ()
	def __dir__(cls, /) -> list[str]: ...

class DocumentedIntConstants(int, DocumentedConstants): ...
class DocumentedNumericConstants(float, DocumentedConstants): ...
class DocumentedStrConstants(str, DocumentedConstants): ...
class DocumentedSetConstants(frozenset, DocumentedConstants): ...
