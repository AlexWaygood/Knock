from __future__ import annotations

from typing import Sequence, TYPE_CHECKING
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from pygame.time import delay, get_ticks as GetTicks
from src.display.colours import ColourScheme

if TYPE_CHECKING:
	from src.special_knock_types import Colour, OptionalColours


class Fader:
	__slots__ = 'Fade', 'StartTime', 'EndTime', 'FadeColour1', 'FadeColour2', 'colour', 'TimeToTake', 'lock'

	colour_scheme: OptionalColours = None

	def __init__(self, colour: str, *args, **kwargs):
		self.Fade = False
		self.StartTime = 0
		self.EndTime = 0
		self.colour = self.colour_scheme[colour]
		self.FadeColour1 = tuple()
		self.FadeColour2 = tuple()
		self.TimeToTake = 0

	def DoFade(self,
	           colour1: Colour,
	           colour2: Colour,
	           TimeToTake: int):

		self.Fade = True
		self.StartTime = GetTicks()
		self.FadeColour1 = colour1
		self.FadeColour2 = colour2
		self.TimeToTake = TimeToTake
		self.EndTime = GetTicks() + TimeToTake

	def GetColourHelper(
			self,
			ElapsedTime: int,
			i: int
	):
		Step = self.FadeColour1[i] + (((self.FadeColour2[i] - self.FadeColour1[i]) / self.TimeToTake) * ElapsedTime)
		if Step < 0:
			return 0
		if Step > 255:
			return 255
		return Step

	def GetColour(self):
		if not self.Fade:
			return self.colour

		if (Time := GetTicks()) > self.EndTime:
			self.Fade = False
			self.colour = self.FadeColour2
			return self.FadeColour2

		Elapsed = Time - self.StartTime
		return [self.GetColourHelper(Elapsed, i) for i, _ in enumerate(self.FadeColour1)]

	@classmethod
	def AddColourScheme(cls):
		cls.colour_scheme: OptionalColours = ColourScheme.OnlyColourScheme


class ColourFader(Fader):
	__slots__ = tuple()

	def __call__(
			self,
			colour1: str,
			colour2: str,
			TimeToTake: int
	):

		self.DoFade(self.colour_scheme[colour1], self.colour_scheme[colour2], TimeToTake)
		delay(TimeToTake)
		while self.Fade:
			delay(50)


class OpacityFader(Fader):
	__slots__ = tuple()

	AllOpacityFaders = {}

	def __init__(
			self,
			StartOpacity: str,
			name: str
	):
		super().__init__(StartOpacity)
		self.AllOpacityFaders[name] = self

	def FadeInProgress(self):
		return self.GetColour()[0] if self.Fade else False

	def GetOpacity(self):
		return self.GetColour()[0]

	@classmethod
	def CardFade(
			cls,
			Surfaces: Sequence[str],
			TimeToTake: int,
			FadeIn: bool
	):

		Opacity1, Opacity2 = (255, 0) if FadeIn else (0, 255)

		for s in Surfaces:
			cls.AllOpacityFaders[s].DoFade((Opacity1,), (Opacity2,), TimeToTake)

		delay(TimeToTake)

		while any(cls.AllOpacityFaders[s].Fade for s in Surfaces):
			delay(50)
