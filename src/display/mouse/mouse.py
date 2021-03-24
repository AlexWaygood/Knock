from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.display.mouse.cursors import NWArrow, NEArrow, DownArrow, UpArrow, SWArrow, SEArrow, LeftArrow, RightArrow
from src.display.surface_coordinator import SurfaceCoordinator

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.mouse import get_pressed, get_pos, set_cursor
from pygame.time import get_ticks as GetTicks
from pygame.cursors import compile, diamond
from pygame.locals import SYSTEM_CURSOR_HAND, SYSTEM_CURSOR_NO, SYSTEM_CURSOR_WAIT, SYSTEM_CURSOR_ARROW

if TYPE_CHECKING:
	from src.special_knock_types import Position
	from src.display.input_context import InputContext


@dataclass(eq=False, unsafe_hash=True)
class Scrollwheel:
	# Repr automatically defined as it's a dataclass!

	__slots__ = 'IsDown', 'DownPos', 'DownTime', 'OriginalDownTime'

	IsDown: bool
	DownPos: Position
	DownTime: int
	OriginalDownTime: int

	def clicked(self):
		self.IsDown = not self.IsDown
		if self.IsDown:
			self.DownPos = get_pos()
			self.DownTime = self.OriginalDownTime = GetTicks()

	def ComesUp(self):
		self.IsDown = False

	def IsMoving(self):
		return self.IsDown and GetTicks() > self.OriginalDownTime + 20

	def GetMovement(self):
		# noinspection PyTupleAssignmentBalance
		DownX, DownY, MouseX, MouseY = *self.DownPos, *get_pos()
		return ((DownX - MouseX) / 200), ((DownY - MouseY) / 200)


class Mouse(SurfaceCoordinator):
	__slots__ = 'Scrollwheel', 'cursor', 'ScoreboardButton', 'CardHoverID', 'click', 'CardsInHand', 'context'

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

	def __init__(
			self,
			ScoreboardButton,
			context: InputContext
	):
		self.context = context
		self.Scrollwheel = Scrollwheel(False, tuple(), 0, 0)
		self.cursor = 'default'
		self.ScoreboardButton = ScoreboardButton
		self.CardHoverID = ''
		self.click = False
		self.CardsInHand = self.player.Hand
		self.AllSurfaces.append(self)

	# **kwargs included because it might be passed ForceUpdate=True
	def Update(self, **kwargs):
		if (cur := self.CursorValue()) != self.cursor:
			self.cursor = cur
			set_cursor(*cur)

		if self.click:
			if self.context.ClickToStart:
				self.game.TimeToStart()

			elif (
					self.context.TrickClickNeeded
					and self.cursor == 'Hand'
					and self.player.PosInTrick == len(self.game.PlayedCards)
			):
				self.game.ExecutePlay(self.CardHoverID, self.player.playerindex)

	def CursorValue(self):
		if self.client.ConnectionBroken:
			return self.Wait

		MousePos = get_pos()

		if self.Scrollwheel.IsDown:
			# noinspection PyTupleAssignmentBalance
			DownX, DownY, MouseX, MouseY = *self.Scrollwheel.DownPos, *MousePos
			if MouseX < (DownX - 50):
				if MouseY < (DownY - 50):
					return self.NW
				if MouseY > (DownY + 50):
					return self.SW
				return self.W

			if MouseX > (DownX + 50):
				if MouseY < (DownY - 50):
					return self.NE
				if MouseY > (DownY + 50):
					return self.SE
				return self.E

			if MouseY > (DownY + 50):
				return self.S
			if MouseY < (DownY - 50):
				return self.N
			return self.Diamond

		if get_pressed(5)[0] and get_pressed(5)[2]:  # or self.ScoreboardButton.colliderect.collidepoint(*MousePos))
			return self.Hand

		Condition = all((
			self.CardsInHand,
			self.game.TrickInProgress,
			self.game.WhoseTurnPlayerIndex == self.player.playerindex
		))

		if not Condition:
			return self.default

		cur = self.default
		for card in self.CardsInHand:
			if card.colliderect.collidepoint(*MousePos):
				self.CardHoverID = f'{card!r}'
				cur = self.Hand

				if PlayedCards := self.game.PlayedCards:
					SuitLed = PlayedCards[0].Suit
					Condition = any(UnplayedCard.Suit == SuitLed for UnplayedCard in self.CardsInHand)

					if card.Suit != SuitLed and Condition:
						cur = self.IllegalMove
		return cur

	def __repr__(self):
		return f'''Object representing current state of the mouse. Current state:
-cursor: {self.cursor}
-CardHoverID: {self.CardHoverID}
-click: {self.click}

'''
