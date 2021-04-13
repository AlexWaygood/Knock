from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.display.surface_coordinator import SurfaceCoordinator
from src.display.mouse.cursors import Cursors

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.mouse import get_pressed, get_pos, set_cursor
from pygame.time import get_ticks as GetTicks

if TYPE_CHECKING:
	from src.special_knock_types import Position
	from src.display.input_context import InputContext


def ScrollwheelDownCursor(
		ScrollwheelDownX: float,
		ScrollwheelDownY: float,
		MousePosX: int,
		MousePosY: int,
		MAGIC_NUMBER: int = 50
):
	if MousePosX < (ScrollwheelDownX - MAGIC_NUMBER):
		if MousePosY < (ScrollwheelDownY - MAGIC_NUMBER):
			return Cursors.NorthWest
		if MousePosY > (ScrollwheelDownY + MAGIC_NUMBER):
			return Cursors.SouthWest
		return Cursors.West

	if MousePosX > (ScrollwheelDownX + MAGIC_NUMBER):
		if MousePosY < (ScrollwheelDownY - MAGIC_NUMBER):
			return Cursors.NorthEast
		if MousePosY > (ScrollwheelDownY + MAGIC_NUMBER):
			return Cursors.SouthEast
		return Cursors.East

	if MousePosY > (ScrollwheelDownY + MAGIC_NUMBER):
		return Cursors.South
	if MousePosY < (ScrollwheelDownY - MAGIC_NUMBER):
		return Cursors.North
	return Cursors.Diamond


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

	def __init__(
			self,
			ScoreboardButton,
			context: InputContext
	):
		self.context = context
		self.Scrollwheel = Scrollwheel(False, tuple(), 0, 0)
		self.cursor = Cursors.Default
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
			return Cursors.Wait

		MousePos = get_pos()

		if self.Scrollwheel.IsDown:
			return ScrollwheelDownCursor(*self.Scrollwheel.DownPos, *MousePos)

		if get_pressed(5)[0] and get_pressed(5)[2]:  # or self.ScoreboardButton.colliderect.collidepoint(*MousePos))
			return Cursors.Hand

		Condition = all((
			self.CardsInHand,
			self.game.TrickInProgress,
			self.game.WhoseTurnPlayerIndex == self.player.playerindex
		))

		if not Condition:
			return Cursors.Default

		cur = Cursors.Default
		for card in self.CardsInHand:
			if card.colliderect.collidepoint(*MousePos):
				self.CardHoverID = repr(card)
				cur = Cursors.Hand

				if PlayedCards := self.game.PlayedCards:
					SuitLed = PlayedCards[0].Suit
					Condition = any(UnplayedCard.Suit == SuitLed for UnplayedCard in self.CardsInHand)

					if card.Suit != SuitLed and Condition:
						cur = Cursors.IllegalMove
		return cur

	def __repr__(self):
		return f'''Object representing current state of the mouse. Current state:
-cursor: {self.cursor}
-CardHoverID: {self.CardHoverID}
-click: {self.click}

'''
