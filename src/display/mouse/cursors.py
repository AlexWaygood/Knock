from __future__ import annotations
from typing import TYPE_CHECKING, NamedTuple, Final

# noinspection PyUnresolvedReferences
from src import pre_pygame_import, Position
# noinspection PyPep8Naming
from pygame.cursors import (
	diamond as DIAMOND_CURSOR,
	compile as cursor_compile
)

from pygame.locals import SYSTEM_CURSOR_HAND, SYSTEM_CURSOR_NO, SYSTEM_CURSOR_WAIT, SYSTEM_CURSOR_ARROW

if TYPE_CHECKING:
	from src.special_knock_types import Position, ArrowCursor, Cursor_Type


WEST_ARROW = (
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                             XXXXXXXXXXXXXXXXXX                 ',
	'                      XX                                                                 XXXXXX XXXXX XXXXXX                    ',
	'                 XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX                    ',
	'                     XXX                                                                XXXXXXXXXXXXXXXXXXX                     ',
	'                                                                                            XXXXXX XXXXX XXXXXX                 ',
	'                                                                                                                                ',
	)

EAST_ARROW = (
	'                                                                                                                                ',
	'                 XXXXXX XXXXXXXXXXXX                                                                                            ',
	'                     XXXXXX XXXXXXXXXXXX                                                                 XX                     ',
	'                     XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX                 ',
	'                      XXXXXX XXXXXXXXXXXX                                                                XXX                    ',
	'                  XXXXXXXXXXXXXXXXXXX                                                                                           ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	)

NORTH_ARROW = (
	'                                                                                                                                ',
	'                                                                XX                                                              ',
	'                                                              XXXXX                                                             ',
	'                                                             X  X  XX                                                           ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                X                                                               ',
	'                                                                XX                                                              ',
	'                                                              XXXXX                                                             ',
	'                                                            XXXXXXXXX                                                           ',
	'                                                           XXXXXXXXXXXX                                                         ',
	'                                                          XXX XXXXXXXXX                                                         ',
	'                                                          XXXXX XXXXX X                                                         ',
	'                                                          XXXXXXXXX XXX                                                         ',
	'                                                          XXXXXXXXXXXXX                                                         ',
	'                                                           XXXX X  XXXX                                                         ',
	'                                                          XXX       XXX                                                         ',
	'                                                          XX          X                                                         ',
	'                                                                                                                                '
	)

SOUTH_ARROW = (
	'                                                                                                                                ',
	'                                                          XX        XXX                                                         ',
	'                                                          XXXX     XXX                                                          ',
	'                                                          XXXXXXXXXXXX                                                          ',
	'                                                          XXXXXXXXXXXX                                                          ',
	'                                                          XXXXXXXXXXXX                                                          ',
	'                                                          XXXXXXXXXXXX                                                          ',
	'                                                          XXXXXXXXXXXXX                                                         ',
	'                                                           XXXXXXXXXX                                                           ',
	'                                                             XXXXXXX                                                            ',
	'                                                              XXXX                                                              ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                               XX                                                               ',
	'                                                             XXXXXX                                                             ',
	'                                                              XXXX                                                              ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	)


SW_ARROW = (
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                             X                                  ',
	'                                                                                          XXX                                   ',
	'                                                                                        XXXXX                                   ',
	'                                                                                      XXXXXX  X                                 ',
	'                                                                                   XXXXX XXXXXXXXXXXX                           ',
	'                                                                                 XXX XX XXXXXXXXX                               ',
	'                                                                                XXXXXXXXXXXXXXXX                                ',
	'                                                                                XXXXXXXXX XXXX                                  ',
	'                                                                               XXXXXXXXXXXX                                     ',
	'                                                                              XXXXX                                             ',
	'                                                                            XX                                                  ',
	'                                                                          X                                                     ',
	'                                                                       XX                                                       ',
	'                                                                     X                                                          ',
	'                                                                  XX                                                            ',
	'                                                                X                                                               ',
	'                                                             XX                                                                 ',
	'                                                          XX                                                                    ',
	'                                                        XX                                                                      ',
	'                                                      X                                                                         ',
	'                                                   XX                                                                           ',
	'                                                XX                                                                              ',
	'                                              XX                                                                                ',
	'                                            X                                                                                   ',
	'                                         XX                                                                                     ',
	'                                       X                                                                                        ',
	'                                XX  XX                                                                                          ',
	'                                XXX                                                                                             ',
	'                               XXXXX                                                                                            ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                '
	)

SE_ARROW = (
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                  X                                                                                             ',
	'                                   XXX                                                                                          ',
	'                                   XXXXX                                                                                        ',
	'                                 X  XXX XX                                                                                      ',
	'                           XXXXXXX XXXXXXXXXX                                                                                   ',
	'                              XXXXXXXXXXXXXXXXX                                                                                 ',
	'                                XXXXXXXXXXXXXXXX                                                                                ',
	'                                   XX XXXXXX XXX                                                                                ',
	'                                     XXXXXXXXXXXX                                                                               ',
	'                                          XXXXXXXX                                                                              ',
	'                                                  XX                                                                            ',
	'                                                    XX                                                                          ',
	'                                                       XX                                                                       ',
	'                                                          X                                                                     ',
	'                                                            XX                                                                  ',
	'                                                               X                                                                ',
	'                                                                 XX                                                             ',
	'                                                                   XX                                                           ',
	'                                                                      XX                                                        ',
	'                                                                        XX                                                      ',
	'                                                                           XX                                                   ',
	'                                                                             XX                                                 ',
	'                                                                                XX                                              ',
	'                                                                                  XX                                            ',
	'                                                                                     XX                                         ',
	'                                                                                       XX                                       ',
	'                                                                                          XX   X                                ',
	'                                                                                            XXXXX                               ',
	'                                                                                          XXXXXXXX                              ',
	'                                                                                           XXXXXXXX                             ',
	'                                                                                          XX XX XX                              ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                '
	)

NE_ARROW = (
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                          XXXXXXX                               ',
	'                                                                                            XX XX                               ',
	'                                                                                         XX    X                                ',
	'                                                                                       XX                                       ',
	'                                                                                    XX                                          ',
	'                                                                                  XX                                            ',
	'                                                                               XX                                               ',
	'                                                                             XX                                                 ',
	'                                                                          XX                                                    ',
	'                                                                        XX                                                      ',
	'                                                                     XX                                                         ',
	'                                                                   XX                                                           ',
	'                                                                 X                                                              ',
	'                                                              XX                                                                ',
	'                                                           XX                                                                   ',
	'                                                         XX                                                                     ',
	'                                                      XX                                                                        ',
	'                                                    XX                                                                          ',
	'                                                 XX                                                                             ',
	'                                       XXXXXXXXXXX                                                                              ',
	'                                    XXXXXXX  XXXX                                                                               ',
	'                                  XXXXXXXXXXXXXXX                                                                               ',
	'                               XXXXX XXXXXXX XXX                                                                                ',
	'                             XXXXXXXXXXX XXXXXX                                                                                 ',
	'                          XXXX     X XXXXXXXX                                                                                   ',
	'                            X       XXXXXX                                                                                      ',
	'                                    XXX                                                                                         ',
	'                                   XX                                                                                           ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                '
	)

NW_ARROW = (
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                               XXX                                                                                              ',
	'                                XXX  X                                                                                          ',
	'                                 X  XX                                                                                          ',
	'                                      XX                                                                                        ',
	'                                         XX                                                                                     ',
	'                                           XX                                                                                   ',
	'                                              XX                                                                                ',
	'                                                XX                                                                              ',
	'                                                   XX                                                                           ',
	'                                                     XX                                                                         ',
	'                                                        XX                                                                      ',
	'                                                          XX                                                                    ',
	'                                                             XX                                                                 ',
	'                                                               XX                                                               ',
	'                                                                  XX                                                            ',
	'                                                                    XX                                                          ',
	'                                                                       XX                                                       ',
	'                                                                         XX                                                     ',
	'                                                                            XX                                                  ',
	'                                                                              XXX                                               ',
	'                                                                               XXXXXXXXXXXX                                     ',
	'                                                                                XXXXXXXXXXXXX                                   ',
	'                                                                                XXXXXXXXXXXXXXXX                                ',
	'                                                                                 XXX XXXXXXXXXX XX                              ',
	'                                                                                   XXXXX XXXXXXXXXXXX                           ',
	'                                                                                      XXXXXXXXX                                 ',
	'                                                                                        XXXXX                                   ',
	'                                                                                          XXXX                                  ',
	'                                                                                             X X                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                ',
	'                                                                                                                                '
	)


NORTH_ARROW_HOTSPOT: Final = Position(64, 0)
NE_ARROW_HOTSPOT: Final    = Position(97, 8)
EAST_ARROW_HOSTPOT: Final  = Position(111, 4)
SE_ARROW_HOSTPOT: Final    = Position(99, 36)
SOUTH_ARROW_HOTSPOT: Final = Position(64, 39)
SW_ARROW_HOTSPOT: Final    = Position(31, 35)
WEST_ARROW_HOTSPOT: Final  = Position(17, 4)
NW_ARROW_HOTSPOT: Final    = Position(32, 6)


def make_cursor(arrow: ArrowCursor, hotspot: Position) -> Cursor_Type:
	return (len(arrow[0]), len(arrow)), hotspot, *cursor_compile(arrow)


class Cursors(NamedTuple):
	north:          Cursor_Type     =   make_cursor(NORTH_ARROW,    NORTH_ARROW_HOTSPOT)
	northeast:      Cursor_Type     =   make_cursor(NE_ARROW,       NE_ARROW_HOTSPOT)
	east:           Cursor_Type     =   make_cursor(EAST_ARROW,     EAST_ARROW_HOSTPOT)
	southeast:      Cursor_Type     =   make_cursor(SE_ARROW,       SE_ARROW_HOSTPOT)
	south:          Cursor_Type     =   make_cursor(SOUTH_ARROW,    SOUTH_ARROW_HOTSPOT)
	southwest:      Cursor_Type     =   make_cursor(SW_ARROW,       SW_ARROW_HOTSPOT)
	west:           Cursor_Type     =   make_cursor(WEST_ARROW,     WEST_ARROW_HOTSPOT)
	northwest:      Cursor_Type     =   make_cursor(NW_ARROW,       NW_ARROW_HOTSPOT)

	diamond:        Cursor_Type     =   DIAMOND_CURSOR

	hand:           Cursor_Type     =   (SYSTEM_CURSOR_HAND,)
	default:        Cursor_Type     =   (SYSTEM_CURSOR_ARROW,)
	illegal_move:   Cursor_Type     =   (SYSTEM_CURSOR_NO,)
	wait:           Cursor_Type     =   (SYSTEM_CURSOR_WAIT,)


cursors = Cursors()
