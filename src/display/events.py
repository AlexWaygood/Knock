from src import DocumentedEnum
from pygame.event import custom_type as custom_pygame_event


class KnockEvents(int, DocumentedEnum):
	"""Custom events specific to this game that will be injected into the PyGame event queue."""

	# Events relating to updating various surfaces.
	UPDATE_BOARD_SURF = 'Event signifying the board surf needs to be repainted', custom_pygame_event()
	UPDATE_HAND_SURF = 'Event signifying the hand surf needs to be repainted', custom_pygame_event()
	UPDATE_SCOREBOARD_SURF = 'Event signifying the scoreboard surf needs to be repainted', custom_pygame_event()
	UPDATE_TRUMP_CARD_SURF = 'Event signifying the trumpcard surf needs to be repainted', custom_pygame_event()

