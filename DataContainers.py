from HelperFunctions import PrintableCharactersPlusSpace

from dataclasses import dataclass
from typing import List, Any
from queue import Queue
from os import environ
from itertools import accumulate

environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pg
from pygame.time import delay


@dataclass
class Errors:
	__slots__ = 'Messages', 'ThisPass', 'StartTime', 'Pos', 'Title'

	Messages: List
	ThisPass: List
	StartTime: int
	Pos: tuple
	Title: Any


class Queues:
	__slots__ = 'ServerComms', 'SurfaceUpdates'

	def __init__(self):
		self.ServerComms = Queue()
		self.SurfaceUpdates = Queue()


@dataclass
class UserInput:
	__slots__ = 'Text', 'click'

	Text: str
	click: bool

	def AddInputText(self, event):
		if (EvUnicode := event.unicode) in PrintableCharactersPlusSpace:
			try:
				self.Text += EvUnicode
			finally:
				return None

		elif not self.Text:
			return None

		if (EvKey := event.key) == pg.K_BACKSPACE:
			self.Text = self.Text[:-1]

		elif EvKey == pg.K_RETURN:
			Text = self.Text
			self.Text = ''
			return Text


class Typewriter:
	__slots__ = 'RenderedSteps', 'Index', 'Rect', 'Q'

	def __init__(self):
		self.RenderedSteps = []
		self.Index = -1
		self.Rect = None
		self.Q = Queue()

	def Type(self, text, WaitAfterwards=1200):
		self.Q.put(text)

		while not self.Q.empty():
			delay(100)

		for letter in text:
			self.Index += 1
			delay(30)

		if WaitAfterwards:
			delay(WaitAfterwards)

		self.Index = -1

	def RenderStepsIfNeeded(self, font):
		if not self.Q.empty():
			self.Rect = pg.Rect((0, 0), font.size((text := self.Q.get())))
			self.RenderedSteps = [font.render(step, False, (0, 0, 0)) for step in accumulate(text)]

	def GetTypedText(self, RectCenter):
		if self.Index == -1:
			return []

		TypewrittenText = self.RenderedSteps[self.Index]
		self.Rect.center = RectCenter
		SubRect = TypewrittenText.get_rect()
		SubRect.topleft = self.Rect.topleft
		return [(TypewrittenText, SubRect)]


@dataclass
class Scrollwheel:
	__slots__ = 'IsDown', 'DownPos', 'DownTime', 'OriginalDownTime'

	IsDown: bool
	DownPos: tuple
	DownTime: int
	OriginalDownTime: int

	def clicked(self, MousePos, Time):
		self.IsDown = not self.IsDown
		if self.IsDown:
			self.DownPos = MousePos
			self.DownTime = self.OriginalDownTime = Time


@dataclass
class FireworkVars:
	__slots__ = 'LastFirework', 'EndTime', 'RandomAmount'

	LastFirework: int
	EndTime: int
	RandomAmount: int



