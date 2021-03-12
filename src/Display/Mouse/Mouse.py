from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.DataStructures import DictLike
from src.Display.Mouse.Cursors import NWArrow, NEArrow, DownArrow, UpArrow, SWArrow, SEArrow, LeftArrow, RightArrow
from src.Display.AbstractSurfaces.SurfaceCoordinator import SurfaceCoordinator

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from pygame.cursors import compile, diamond
from pygame.locals import SYSTEM_CURSOR_HAND, SYSTEM_CURSOR_NO, SYSTEM_CURSOR_WAIT, SYSTEM_CURSOR_ARROW

if TYPE_CHECKING:
	from src.SpecialKnockTypes import Position


@dataclass
class Scrollwheel:
	# Repr automatically defined as it's a dataclass!

	__slots__ = 'IsDown', 'DownPos', 'DownTime', 'OriginalDownTime'

	IsDown: bool
	DownPos: Position
	DownTime: int
	OriginalDownTime: int

	def clicked(self,
	            MousePos: Position,
	            Time: int):

		self.IsDown = not self.IsDown
		if self.IsDown:
			self.DownPos = MousePos
			self.DownTime = self.OriginalDownTime = Time


class Mouse(SurfaceCoordinator, DictLike):
	__slots__ = 'Scrollwheel', 'cursor', 'ScoreboardButton', 'CardHoverID', 'click', 'CardsInHand'

	N   =   ((128, 40), (64, 0),    *compile(UpArrow))
	NE  =   ((128, 40), (97, 8),    *compile(NEArrow))
	E   =   ((128, 8),  (111, 4),   *compile(RightArrow))
	SE  =   ((128, 40), (99, 36),   *compile(SEArrow))
	S   =   ((128, 40), (64, 39),   *compile(DownArrow))
	SW  =   ((128, 40), (31, 35),   *compile(SWArrow))
	W   =   ((128, 8),  (17, 4),    *compile(LeftArrow))
	NW  =   ((128, 40), (32, 6),    *compile(NWArrow))

	Diamond     = diamond
	Hand        = (SYSTEM_CURSOR_HAND,)
	default     = (SYSTEM_CURSOR_ARROW,)
	IllegalMove = (SYSTEM_CURSOR_NO,)
	Wait        = (SYSTEM_CURSOR_WAIT,)

	def __init__(self, ScoreboardButton):
		self.Scrollwheel = Scrollwheel(False, tuple(), 0, 0)
		self.cursor = 'default'
		self.ScoreboardButton = ScoreboardButton
		self.CardHoverID = ''
		self.click = False
		self.CardsInHand = self.player.Hand

	def __repr__(self):
		return f'''Object representing current state of the mouse. Current state:
-cursor: {self.cursor}
-CardHoverID: {self.CardHoverID}
-click: {self.click}

'''

	# **kwargs included so that the method still works
	# if it's passed an unexpected argument from the SurfaceCoordinator classmethod

	def Update(self, **kwargs):
		MousePos = pg.mouse.get_pos()

		if self.Scrollwheel.IsDown:
			# noinspection PyTupleAssignmentBalance
			DownX, DownY, MouseX, MouseY = *self.Scrollwheel.DownPos, *MousePos
			if MouseX < (DownX - 50):
				if MouseY < (DownY - 50):
					cur = 'NW'
				elif MouseY > (DownY + 50):
					cur = 'SW'
				else:
					cur = 'W'
			elif MouseX > (DownX + 50):
				if MouseY < (DownY - 50):
					cur = 'NE'
				elif MouseY > (DownY + 50):
					cur = 'SE'
				else:
					cur = 'E'
			elif MouseY > (DownY + 50):
				cur = 'S'
			elif MouseY < (DownY - 50):
				cur = 'N'
			else:
				cur = 'Diamond'

		elif (
				(pg.mouse.get_pressed(5)[0] and pg.mouse.get_pressed(5)[2])
				or self.ScoreboardButton.colliderect.collidepoint(*MousePos)
		):
			cur = 'Hand'

		elif (
				self.CardsInHand
				and self.game.TrickInProgress
				and self.game.WhoseTurnPlayerIndex == self.player.playerindex
		):
			cur = 'default'
			for card in self.CardsInHand:
				if card.colliderect.collidepoint(*MousePos):
					self.CardHoverID = f'{card!r}'
					cur = 'Hand'

					if PlayedCards := self.game.PlayedCards:
						SuitLed = PlayedCards[0].Suit
						Condition = any(UnplayedCard.Suit == SuitLed for UnplayedCard in self.CardsInHand)

						if card.Suit != SuitLed and Condition:
							cur = 'IllegalMove'

		else:
			cur = 'default'

		if cur != self.cursor:
			self.cursor = cur
			pg.mouse.set_cursor(*self[cur])
