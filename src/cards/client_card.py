"""An enumeration representing the clientside simulation of a pack of cards."""

from __future__ import annotations

from os import path
from typing import TYPE_CHECKING, Final, Mapping, Optional, Any, TypeVar
from functools import lru_cache
from fractions import Fraction

from PIL import Image
from src import Position, cached_readonly_property
from src.cards.abstract_card import AbstractCard, CardEnumMeta, next_card, CardEnumConstructor
from src.cards.card_typing_constants import PossibleWinValues
from src.config import card_resize_ratio_at_game_start
from src.cards import Suit
from src.display.window import Window, GameDimensions
from immutables import Map
from aenum import skip

from pygame import Surface
from pygame.transform import rotozoom
from pygame.image import fromstring as pg_image_fromstring

if TYPE_CHECKING:
	from src.players.players_client import ClientPlayer


CardImageMap = Mapping[str, Surface]
PATH_TO_CARD_IMAGES: Final = path.join('Images', 'Cards', 'Compressed')


def pg_image_from_file(card_id: str, resize_ratio: Fraction) -> Surface:
	"""Return a pygame object representing a card image.

	Parameters
	----------
	card_id: str
		A string, with length of either 2 or three,
		that identifies the rank and suit of a given card from a standard deck.
		E.g. the card_ID for the Jack of Diamonds would be 'J♢',
		while the card_ID for the 10 of Hearts would be '10♡'.
	resize_ratio: fraction.Fraction
		A `fraction.Fraction` object that specifies the ratio
		by which the image should be resized before being converted into a pygame.Surface object.

	Returns
	-------
	A pygame.Surface object, which will be that card's visual representation during the game.
	"""
	im = Image.open(path.join(PATH_TO_CARD_IMAGES, f'{card_id}.jpg')).convert("RGB")
	im = im.resize((int(im.size[0] / resize_ratio), int(im.size[1] / resize_ratio)))
	return pg_image_fromstring(im.tobytes(), im.size, im.mode).convert()


@lru_cache
def resize_cards(*card_images: tuple[str, Surface], resize_ratio: Fraction) -> CardImageMap:
	"""Resize the associated pygame.Surface object for each card in the pack.

	Parameters
	----------
	resize_ratio: fraction.Fraction
		A `fraction.Fraction` object that specifies the ratio by which the card images need to be resized.
	card_images: typing.Sequence[tuple[str, pygame.Surface]]
		A tuple of tuples.
		Each inner tuple consists of a card_ID string (e.g. 'J♢' for the Jack of Diamonds, '10♡' for the 10 of Hearts),
		and the `pygame.Surface` object associated with that card.

	Returns
	-------
	A [str, pygame.Surface] `immutables.Map` object mapping card_IDs to card images.
	"""
	if resize_ratio == 1:
		return Map(card_images)
	return Map({ID: rotozoom(card_image, 0, (1 / resize_ratio)) for ID, card_image in card_images})


# noinspection PyTypeChecker
M = TypeVar('M', bound='ClientCardEnumMeta')


class ClientCardEnumMeta(CardEnumMeta):
	"""Metaclass for the `ClientCard` enum below."""

	_card_images: CardImageMap = skip(None)

	@cached_readonly_property
	def base_card_images(cls, /) -> CardImageMap:
		"""A one-time constant that is calculated at the start of the game."""

		# This mapping CANNOT be calculated on import
		# as this module needs to be imported prior to `pygame.display` being initialised.

		return Map({
			card_value: pg_image_from_file(card_concise_name, card_resize_ratio_at_game_start)
			for card_value, card_concise_name, *_ in CardEnumConstructor.construct_pack()
		})

	@property
	def card_images(cls, /) -> CardImageMap:
		"""Get the card images at the size they are with the user's current zoom level."""

		return cls._card_images

	@Window.on_window_resize
	def update_images(cls, game_dimensions: GameDimensions) -> None:
		"""Resize the card images according to a certain ratio if the player is zooming in or out.

		This function is registered with the `Window` class through the `Window.on_window_resize` decorator,
		such that it is called every time the window is resized.

		Parameters
		----------
		game_dimensions: GameDimensions
			A `NamedTuple` containing the new dimensions of the game.

		Returns
		-------
		None

		Modifies
		--------
		cls._card_images: A read-only map of card IDs to card images.
		"""

		cls._card_images = resize_cards(
			*cls.base_card_images.items(),
			resize_ratio=game_dimensions.card_image_resize_ratio
		)


class ClientCard(AbstractCard, metaclass=ClientCardEnumMeta):
	"""An enum representing a pack of cards of the standard French deck (clientside version).

	While the serverside simulation of the pack of cards is entirely immutable,
	members of the clientside pack have some mutable attributes:
	-   `rect`: The rectangle on a specific surface (position relative to that surface) where that card currently lies.
	-   `collide_rect`: The card's position relative to the GameSurface as a whole (useful for detecting collisions).
	-   `image`: The image associated with this card.

	In addition, members of the clientside pack have one dynamic property:
	-   `surf_and_pos`: The card's (image, rect) returned as a tuple.
	"""

	def __init__(self, *args: Any) -> None:
		super().__init__(*args)
		self.pos_on_surf = Position(0, 0)
		self.pos_on_game = Position(0, 0)
		self.owner: Optional[ClientPlayer] = None

	def get_win_value(self, led_suit: Suit, trump_suit: Suit) -> PossibleWinValues:
		"""Given the suit led and the trump suit for this round, return the "win value" of the card this trick."""
		suit, rank_val = self.suit, self.rank.value

		if suit is led_suit:
			return rank_val
		if suit is trump_suit:
			return rank_val + 13
		return 0

	@property
	def image(self, /) -> Surface:
		"""Return the image associated with the card."""
		return type(self).card_images[self.value]

	@property
	def surf_and_pos(self, /) -> tuple[Surface, Position]:
		"""Return the image and rect associated with the card."""
		return self.image, self.pos_on_surf

	def move_collide_rect(self, x_motion: float, y_motion: float) -> None:
		"""Move the collide_rect attribute of the card in-place."""
		self.pos_on_game = self.pos_on_game.moved(x_motion, y_motion)

	Two_of_Diamonds = next_card()
	Two_of_Clubs = next_card()
	Two_of_Spades = next_card()
	Two_of_Hearts = next_card()

	Three_of_Diamonds = next_card()
	Three_of_Clubs = next_card()
	Three_of_Spades = next_card()
	Three_of_Hearts = next_card()

	Four_of_Diamonds = next_card()
	Four_of_Clubs = next_card()
	Four_of_Spades = next_card()
	Four_of_Hearts = next_card()

	Five_of_Diamonds = next_card()
	Five_of_Clubs = next_card()
	Five_of_Spades = next_card()
	Five_of_Hearts = next_card()

	Six_of_Diamonds = next_card()
	Six_of_Clubs = next_card()
	Six_of_Spades = next_card()
	Six_of_Hearts = next_card()

	Seven_of_Diamonds = next_card()
	Seven_of_Clubs = next_card()
	Seven_of_Spades = next_card()
	Seven_of_Hearts = next_card()

	Eight_of_Diamonds = next_card()
	Eight_of_Clubs = next_card()
	Eight_of_Spades = next_card()
	Eight_of_Hearts = next_card()

	Nine_of_Diamonds = next_card()
	Nine_of_Clubs = next_card()
	Nine_of_Spades = next_card()
	Nine_of_Hearts = next_card()

	Ten_of_Diamonds = next_card()
	Ten_of_Clubs = next_card()
	Ten_of_Spades = next_card()
	Ten_of_Hearts = next_card()

	Jack_of_Diamonds = next_card()
	Jack_of_Clubs = next_card()
	Jack_of_Spades = next_card()
	Jack_of_Hearts = next_card()

	Queen_of_Diamonds = next_card()
	Queen_of_Clubs = next_card()
	Queen_of_Spades = next_card()
	Queen_of_Hearts = next_card()

	King_of_Diamonds = next_card()
	King_of_Clubs = next_card()
	King_of_Spades = next_card()
	King_of_Hearts = next_card()

	Ace_of_Diamonds = next_card()
	Ace_of_Clubs = next_card()
	Ace_of_Spades = next_card()
	Ace_of_Hearts = next_card()


# An alias for the Enum just defined above, so that we can do, e.g., `ClientPack.BLACKS` in other modules.
ClientPack = ClientCard


if __name__ == '__main__':
	from doctest import testmod
	testmod()
