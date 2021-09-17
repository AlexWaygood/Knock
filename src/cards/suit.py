"""An enumeration representing all possible cards_grouped_by_suits_dict a card could have in a standard French deck."""

from __future__ import annotations

from aenum import MultiValue, Unique

from src.cards.card_suit_rank_abc import SuitOrRankEnum
from src import cached_readonly_property
from typing import TypeVar, cast


# noinspection PyTypeChecker
S = TypeVar('S', bound='Suit')


# noinspection PyPropertyDefinition
class Suit(SuitOrRankEnum, settings=(MultiValue, Unique)):
	# noinspection PyUnresolvedReferences
	"""The suit of a card in a standard French deck. All `Suit` members have `str` values of length 1.
	Suit members can be accessed programmatically via their value or the first initial of their full name.

	Examples
	--------
	>>> Suit['Diamonds'] is Suit('D') is Suit('♢') is Suit.Diamonds is Suit(Suit.Diamonds)
	True
	"""

	Diamonds = '♢', 'D'
	Clubs = '♣', 'C'
	Spades = '♠', 'S'
	Hearts = '♡', 'H'

	@property
	def concise_name(self, /) -> str:
		"""Return the concise name when __format__ is passed the specifier 'c' or 'concise'.

		Examples
		--------
		>>> f'{Suit.Diamonds:concise}'
		'♢'
		>>> print(f'{Suit.Clubs:concise}')
		♣
		"""

		return self.value

	@property
	def verbose_name(self, /) -> str:
		"""Return the verbose name when __format__ is passed the specifier 'verbose'.

		Examples
		--------
		>>> print(f'{Suit.Diamonds:verbose}')
		Diamonds
		>>> f'{Suit.Spades:verbose}'
		'Spades'
		"""

		return self.name

	# noinspection PyPep8Naming
	@classmethod
	@cached_readonly_property
	def BLACKS(cls: type[S], /) -> frozenset[S]:
		"""Frozenset of the two black cards_grouped_by_suits_dict (clubs and spades)"""
		suit_set = frozenset({cls.Clubs, cls.Spades})
		return cast(frozenset[S], suit_set)

	# noinspection PyPep8Naming
	@classmethod
	@cached_readonly_property
	def REDS(cls: type[S], /) -> frozenset[S]:
		"""Frozenset of the two red cards_grouped_by_suits_dict (diamonds and hearts)"""
		suit_set = frozenset({cls.Diamonds, cls.Hearts})
		return cast(frozenset[S], suit_set)

	@cached_readonly_property
	def is_black(self, /) -> bool:
		"""Return True if the suit is black, else False"""
		return self in self.BLACKS

	@cached_readonly_property
	def is_red(self, /) -> bool:
		"""Return True if the suit is red, else False"""
		return self in self.REDS

	@cached_readonly_property
	def other_of_colour(self: S, /) -> S:
		# noinspection PyUnresolvedReferences
		"""For a given suit, return the other suit of that colour.

		Examples
		--------
		>>> Suit('♢').other_of_colour
		Suit(♡)
		>>> type(Suit('♡').other_of_colour)
		<enum 'Suit'>
		>>> Suit('♣').other_of_colour
		Suit(♠)
		>>> type(Suit('♠').other_of_colour)
		<enum 'Suit'>
		>>> bool({s.other_of_colour for s in Suit}.difference(Suit))
		False
		"""

		cls = type(self)
		if self.is_black:
			return cls('♣' if self == '♠' else '♠')
		return cls('♢' if self == '♡' else '♡')


if __name__ == '__main__':
	from doctest import testmod
	testmod()
