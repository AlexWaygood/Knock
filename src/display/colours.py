from src.display.fireworks.firework_vars import FireworkVars
from src.misc import DictLike


# noinspection PyAttributeOutsideInit
class ColourScheme(DictLike):
	__slots__ = 'MenuScreen', 'Scoreboard', 'GamePlay', 'TextDefault'

	Black = (0, 0, 0)
	Maroon = (128, 0, 0)
	Silver = (128, 128, 128)
	LightGrey = (204, 204, 204)
	Black_fade = (0, 0, 0, FireworkVars.FadeRate)
	Orange = (255, 136, 0)

	# Opacities are given as single-item tuples to ensure consistency
	OpaqueOpacity = (255,)
	TranslucentOpacity = (0,)

	OnlyColourScheme = None

	# This is only going to be called once, so we don't need to muck around with singleton patterns etc.
	def __new__(cls, Theme: str):
		cls.OnlyColourScheme = super(ColourScheme, cls).__new__(cls)
		return cls.OnlyColourScheme

	def __init__(self, Theme: str):
		if Theme == 'Classic':
			self.MenuScreen = self.Silver
			self.Scoreboard = self.Silver
			self.GamePlay = self.Maroon
			self.TextDefault = self.Black
		else:
			self.MenuScreen = self.LightGrey
			self.Scoreboard = self.LightGrey
			self.GamePlay = self.Orange
			self.TextDefault = self.Black

	def __repr__(self):
		return '\n'.join((
			'Colour scheme for the game.',
			'\n-'.join(f'{name}: {self[name]}.' for name in ("MenuScreen", "Scoreboard", "GamePlay", "TextDefault")),
			'\n\n'
		))
