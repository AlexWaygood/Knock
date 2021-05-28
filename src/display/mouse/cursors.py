from __future__ import annotations
from typing import TYPE_CHECKING, NamedTuple

# noinspection PyUnresolvedReferences
from src import pre_pygame_import
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


NORTH_ARROW_HOTSPOT = (64, 0)
NE_ARROW_HOTSPOT    = (97, 8)
EAST_ARROW_HOSTPOT  = (111, 4)
SE_ARROW_HOSTPOT    = (99, 36)
SOUTH_ARROW_HOTSPOT = (64, 39)
SW_ARROW_HOTSPOT    = (31, 35)
WEST_ARROW_HOTSPOT  = (17, 4)
NW_ARROW_HOTSPOT    = (32, 6)


def MakeCursor(Arrow: ArrowCursor, Hotspot: Position) -> Cursor_Type:
	return (len(Arrow[0]), len(Arrow)), Hotspot, *cursor_compile(Arrow)


class Cursors(NamedTuple):
	North:          Cursor_Type     =   MakeCursor(NORTH_ARROW, NORTH_ARROW_HOTSPOT)
	NorthEast:      Cursor_Type     =   MakeCursor(NE_ARROW,    NE_ARROW_HOTSPOT)
	East:           Cursor_Type     =   MakeCursor(EAST_ARROW,  EAST_ARROW_HOSTPOT)
	SouthEast:      Cursor_Type     =   MakeCursor(SE_ARROW,    SE_ARROW_HOSTPOT)
	South:          Cursor_Type     =   MakeCursor(SOUTH_ARROW, SOUTH_ARROW_HOTSPOT)
	SouthWest:      Cursor_Type     =   MakeCursor(SW_ARROW,    SW_ARROW_HOTSPOT)
	West:           Cursor_Type     =   MakeCursor(WEST_ARROW,  WEST_ARROW_HOTSPOT)
	NorthWest:      Cursor_Type     =   MakeCursor(NW_ARROW,    NW_ARROW_HOTSPOT)

	Diamond:        Cursor_Type     =   DIAMOND_CURSOR

	Hand:           Cursor_Type     =   (SYSTEM_CURSOR_HAND,)
	Default:        Cursor_Type     =   (SYSTEM_CURSOR_ARROW,)
	IllegalMove:    Cursor_Type     =   (SYSTEM_CURSOR_NO,)
	Wait:           Cursor_Type     =   (SYSTEM_CURSOR_WAIT,)
