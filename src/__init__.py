"""Only importing things that are used both serverside and clientside"""

### MAGIC CLASSES ###
# DocumentedEnum: For enumerations that have per-member docstrings.
# DocumentedConstants: For arbitrary named constants that have per-member docstrings.
# DocumentedPlaceholders: For sentinel objects that have no value but do have docstrings.


# from typing import TYPE_CHECKING
#
# from src.cards import ServerPack, Suit, Rank
# from src.game import Game, events_dict
# from src.initialisation import print_intro_message, maximise_window, configure_logging
# from src.network import Network, get_time
# from src.password_checker import PasswordChecker
# from src.players import sort_hand_in_place, Players, hand
# from src.misc import DictLike, get_date, get_logger
#
# if TYPE_CHECKING:
# 	from src import special_knock_types
from __future__ import annotations

from time import strftime, localtime
from typing import Any, Sequence, NamedTuple, Callable, TypeVar, Literal, cast, ClassVar, final, Annotated
from functools import singledispatchmethod, cache
from aenum import Enum, NamedConstantMeta, NamedConstant, constant
from enum import IntEnum, auto
from abc import abstractmethod
from inspect import getmro
from itertools import count

# noinspection PyTypeChecker
D = TypeVar('D', bound='DocumentedEnum')
# noinspection PyTypeChecker
DI = TypeVar('DI', bound='DocumentedIntEnum')


### DOCUMENTED CONSTANTS ###


def is_dunder(name: str) -> bool:
	"""Returns True if a __dunder__ name, False otherwise."""

	return all((
		len(name) > 4,
		name[:2] == name[-2:] == '__',
		name[2] != '_',
		name[-3] != '_'
	))


def is_sunder(name: str) -> bool:
	"""Returns True if a _sunder_ name, False otherwise."""

	return all((
		len(name) > 2,
		name[0] == name[-1] == '_',
		name[1] != '_',
		name[-2] != '_'
	))


def is_descriptor(obj: Any) -> bool:
	"""Returns True if obj is a descriptor, False otherwise."""

	return any(
		hasattr(obj, method_name)
		for method_name in ('__get__', '__set__', '__delete__')
	)


class _DocumentedConstantDict(dict[str, Any]):
	"""Track constant order, ensure names are not reused, convert all values to constants.

	`NamedConstantMeta` will use the names found in self._names as the Constant names.

	CREDIT GOES to Ethan Furman's code for NamedConstants in his aenum library,
	of which this class is essentially a fork.
	"""

	__slots__ = '_names',

	def __init__(self, /) -> None:
		super().__init__()
		self._names = []

	def __setitem__(self, key: str, value: tuple[Any, str]) -> None:
		"""Changes anything not dundered into a constant.

		If an constant name is used twice, an error is raised; duplicate
		values are not checked for.

		Single underscore (sunder) names are reserved.
		"""

		if is_sunder(key):
			raise ValueError(
				f'_sunder_ names, such as {key}, are reserved for future NamedConstant use'
			)
		elif is_dunder(key) or (key in {'name', 'value'} and key not in self):
			pass
		elif key in self._names:
			# overwriting an existing constant?
			raise TypeError(f'attempt to reuse name: {key}')
		elif key in self:
			# overwriting a descriptor?
			raise TypeError(f'{key} already defined as: {self[key]}')
		else:
			self._names.append(key)
			value = constant(*value)
		super().__setitem__(key, value)


class DocumentedConstantMeta(NamedConstantMeta):
	"""Metaclass for `DocumentedConstants` class"""

	@classmethod
	def __prepare__(metacls, cls_name: str, cls_bases: tuple[type, ...], **kwargs: Any):
		return _DocumentedConstantDict()


class DocumentedConstants(NamedConstant, metaclass=DocumentedConstantMeta):
	"""Enum-like class that forwards on all method-calls to its members' `value` attributes.
	Each member has its own docstring.
	"""

	@property
	def name(self, /) -> str:
		"""Get the name of the constant."""
		return self._name_

	@property
	def value(self, /) -> Any:
		"""Get the value of the constant."""
		return self._value_


# These aliases are to make the type-checkers happy -- see __init__.pyi.
# noinspection PyTypeChecker
DocumentedNumericConstants \
	= DocumentedStrConstants \
	= DocumentedSetConstants \
	= DocumentedIntConstants \
	= DocumentedConstants


### DOCUMENTED PLACEHOLDERS ###


class _PlaceholderDict(dict):
	__slots__ = ()

	def __setitem__(self, key: str, value: Any, /) -> None:
		if key == '__slots__':
			raise ValueError('Cannot define __slots__ in a `Placeholder` class.')
		elif key == '_complete':
			raise ValueError('The name "_complete" is reserved.')
		elif key in self:
			raise ValueError('You cannot have more than one placeholder of the same name in the same class.')

		super().__setitem__(key, value)


class FrozenError(AttributeError):
	"""Base class for `FrozenInstanceError` and `FrozenClassError`."""


class FrozenInstanceError(FrozenError):
	"""Raised when a user attempts to modify a frozen instance at runtime."""


class FrozenClassError(FrozenError):
	"""Raised when a user attempts to modify a frozen class at runtime."""


class DocumentedPlaceholdersMeta(type):
	"""Metaclass for `DocumentedPlaceholders`."""

	@classmethod
	def __prepare__(metacls, name: str, bases: tuple[type, ...]) -> _PlaceholderDict:
		return _PlaceholderDict()

	def __new__(metacls, cls_name: str, cls_bases: tuple[type, ...], cls_dict: _PlaceholderDict):
		# Remove all the private attributes from the cls_dict and add them to an empty dict.
		new_dict = {'_complete': False} | {k: cls_dict.pop(k) for k in tuple(cls_dict.keys()) if k.startswith('_')}

		# Make an empty class
		new_cls = super().__new__(metacls, cls_name, cls_bases, new_dict)

		# Add the members to the class
		for attr_name, attr_doc in cls_dict.items():
			attr_val = object.__new__(new_cls)
			attr_val.__doc__ = attr_doc
			attr_val.name = attr_name
			setattr(new_cls, attr_name, attr_val)

		# Set the class instances as frozen.

		def __setattr__(self, name: str, value: Any) -> None:
			if self._complete:
				raise FrozenInstanceError('Placeholder constant cannot be altered at runtime.')
			super(new_cls, self).__setattr__(name, value)

		new_cls.__setattr__ = __setattr__

		# Set the class as frozen
		new_cls._complete = True

		return new_cls

	def __setattr__(cls, name: str, value: Any) -> None:
		if cls._complete:
			raise FrozenClassError('Placeholder class cannot be altered at runtime.')
		super().__setattr__(name, value)

	def __bool__(self, /) -> Literal[False]:
		return False

	def __repr__(cls, /) -> str:
		return f'<{cls.__name__}>'


class DocumentedPlaceholders(metaclass=DocumentedPlaceholdersMeta):
	"""Always Falsey Enum-like sentinel classes that have nice __repr__/__str__ methods."""

	def __bool__(self, /) -> Literal[False]:
		return False

	def __str__(self, /) -> str:
		return f'<{self.name}>'

	def __repr__(self, /) -> str:
		return f'<{self.__class__.__name__}.{self.name}>'


_marker = object()


class StrEnum(str, Enum):
	"""String Enum."""

	def __str__(self) -> str:
		return self.value


class IntEnumNiceStr(IntEnum):
	"""IntEnum, but with a slightly tweaked `__str__`"""

	def __str__(self) -> str:
		if self.value > -1:
			return str(self.value)
		return f'<{self.name}>'

	def __repr__(self) -> str:
		if self.value > -1:
			return super().__repr__()
		return f'<{self.__class__.__name__}.{self.name}>'


class DocumentedEnum(Enum):
	"""Adapted form of Ethan Furman's recipe for an `Enum` class that has docstrings for each member.
	See https://stackoverflow.com/questions/19330460/how-do-i-put-docstrings-on-enums.
	"""

	@staticmethod
	def __incorrect_value_message(base_cls: type) -> str:
		"""Helper method for raising an error message if an argument of the wrong type is passed to `__new__`"""
		return f"Since you have mixed in {base_cls}, you must provide a value of type '{base_cls.__name__}'"

	@staticmethod
	def _generate_next_value_(number_so_far=count(1)) -> Any:
		"""Empty method that can be optionally overriden in subclasses."""

	def __new__(cls: D, docstring: str, value: Any = _marker, /) -> D:
		# First, work out which __new__ method we need to use

		# noinspection PyTypeChecker
		first_non_enum_base = next(base for base in getmro(cls) if not issubclass(base, Enum))

		# Now, do some type-checking for the `value` parameter we've received, then call __new__.
		# If there's a type that's not `object` and not an `Enum` subclass in the __mro__,
		# then we need to use that type's __new__ method, and the `value` parameter must be an instance of that type.
		# Otherwise, `value` can be of any type, and we should use `object.__new__`.
		if value is _marker:
			if first_non_enum_base is object:
				value = object()
				obj = object.__new__(cls)
			else:
				raise TypeError(cls.__incorrect_value_message(first_non_enum_base))
		elif not isinstance(value, (first_non_enum_base, auto)):
			raise TypeError(cls.__incorrect_value_message(first_non_enum_base))
		else:
			if isinstance(value, auto):
				value = cls._generate_next_value_()
			# noinspection PyTypeChecker
			obj = first_non_enum_base.__new__(cls, value)

		# Now do some standard `Enum`-specific shenanigans, and we're done!
		obj._value_ = value
		obj.__doc__ = docstring
		return obj


AnyFunction = Callable[..., Any]


def cached_readonly_property(func: AnyFunction) -> property:
	"""Make a cached readonly property"""
	return property(cache(func))


def classmethod_property(func: AnyFunction) -> classmethod:
	"""Make a classmethod property"""
	# noinspection PyTypeChecker
	return classmethod(property(func))


def cached_classmethod_property(func: AnyFunction) -> classmethod:
	"""Make a cached classmethod property"""
	# noinspection PyTypeChecker
	return classmethod(property(cache(func)))


def abstract_classmethod(func: AnyFunction) -> classmethod:
	"""Make an abstract classmethod."""
	return classmethod(abstractmethod(func))


def abstract_classmethod_property(func: AnyFunction) -> classmethod:
	"""Make an abstract classmethod property"""
	# noinspection PyTypeChecker
	return classmethod(property(abstractmethod(func)))


class DataclassyReprBase:
	"""Abstract base class for providing dataclass-esque __reprs__"""

	__slots__ = ()

	NON_REPR_SLOTS: ClassVar[frozenset[str]] = frozenset()
	EXTRA_REPR_ATTRS: ClassVar[tuple[str]] = tuple()

	@final
	@cached_readonly_property
	def _repr_attrs(self, /) -> Sequence[str]:
		repr_attrs = []

		for parent in getmro(type(self)):

			repr_attrs.extend(
				s for s in getattr(parent, '__slots__', ())
				if s not in getattr(parent, 'NON_REPR_SLOTS', ())
			)

			repr_attrs.extend(getattr(parent, 'EXTRA_REPR_ATTRS', ()))

		return tuple(repr_attrs)

	@final
	def __repr__(self, /) -> str:
		attrs_str = ', '.join(f'{s}={getattr(self, s)}' for s in self._repr_attrs)
		return f'{self.__class__.__name__}({attrs_str})'


def get_date() -> str:
	"""Get today's date as a formatted string."""
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

	def get_attributes(self, attrs: Sequence[str]) -> Sequence[Any]:
		return [self[attr] for attr in attrs]


def _register(self, cls: type, method=None) -> Callable:
	""""A fix for the bug in `functools.singledispatchmethod`.
	See: https://stackoverflow.com/questions/62696796/singledispatchmethod-and-class-method-decorators-in-python-3-8
	See: https://bugs.python.org/issue39679
	"""

	if hasattr(cls, '__func__'):
		setattr(cls, '__annotations__', cls.__func__.__annotations__)
	return self.dispatcher.register(cls, func=method)


singledispatchmethod.register = _register

# noinspection PyTypeChecker
P = TypeVar('P', bound='Position')


class Vector(NamedTuple):
	"""NamedTuple representing movement from one (x, y) position to another."""
	x_motion: float
	y_motion: float


class Position(NamedTuple):
	"""NamedTuple representing a single (x, y) coordinate as a (<float>, <float>) tuple."""
	x: float
	y: float

	def __rshift__(self: P, other: Annotated[tuple[float, float], "A vector indicating movement"]) -> P:
		"""Return a new instance of this class with the position moved by the specified vector."""

		(x, y), (x_motion, y_motion) = self, other
		return self.__class__((x + x_motion), (y + y_motion))

	__irshift__ = __rshift__

	def replace(self: P, /, *, x: float, y: float) -> P:
		"""Return a new `Position` instance at the specified coordinates."""
		return self._replace(x=x, y=y)

	def replace_x(self: P, /, *, x: float) -> P:
		"""Return a new `Position` instance with the same y-coordinate but a different x-coordinate."""
		old_x, old_y = self
		return self._replace(x=x, y=old_y)

	def replace_y(self: P, /, *, y: float) -> P:
		"""Return a new `Position` instance with the same x-coordinate but a different y-coordinate."""
		old_x, old_y = self
		return self._replace(x=old_x, y=y)


class Dimensions(NamedTuple):
	"""NamedTuple representing the (<width>, <height>) dimensions of a pygame Surface as a (<float>, <float>) tuple."""
	width: float
	height: float


class ConnectionAddress(NamedTuple):
	"""NamedTuple representing the (IP, port) connection address of a client connecting to a server."""
	IP: str
	port: int


class DocumentedMetaclassMixin(type):
	"""Mixin for metaclasses so that classes using the metaclass will have documentation for inherited methods."""

	__slots__ = ()

	# noinspection PyMethodParameters
	def __dir__(cls, /) -> list[str]:
		"""Return a list of the name of all methods we would like documented.

		`__dir__` is overriden as the builtin `help()` function
		does not document methods defined in metaclasses otherwise.
		"""

		all_attrs = cast(list[str], super().__dir__())

		for metacls in type(cls).__mro__:
			all_attrs.extend(
				k for k in metacls.__dict__
				if not (k.startswith('_') and not (k.startswith('__') and k.endswith('__'))) and k not in all_attrs
			)

		return all_attrs


from src import config as rc
